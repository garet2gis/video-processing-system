import asyncio
from multiprocessing import Pool, cpu_count
import numpy as np
from typing import Deque, Any
from ReconnectingRTSPGear.ReconnectingRTSPGear import ReconnectingRTSPGear
from vidgear.gears import StreamGear
from vidgear.gears.helper import reducer
from collections import deque
from datetime import datetime
import requests
import preprocess_frames_functions
import io
from pydantic import BaseModel

producer_config = {
    'bootstrap.servers': 'localhost:9092',
    'enable.idempotence': True,
    'acks': 'all',
    'retries': 100,
    'max.in.flight.requests.per.connection': 5,
    'compression.type': 'snappy',
    'linger.ms': 5,
    'batch.num.messages': 32
}


class NeuroserviceConfig(BaseModel):
    url: str
    buffer_size: int
    preprocess_func_name: str


def produce_file(frames: Any) -> dict[str, io.BytesIO]:
    bytes_image = frames.tobytes()
    stream = io.BytesIO(bytes_image)
    return {"file": stream}


def prediction_request(url: str, data: dict[str, io.BytesIO]) -> str:
    prediction = requests.post(url, files=data)

    return prediction.json()['prediction']


async def start_stream(cameras: dict[int, str], config: dict[int, NeuroserviceConfig], is_stream_enable: bool):
    camera_gears: dict[int, ReconnectingRTSPGear] = {}

    # producer = Producer(producer_config)

    camera_buffers: dict[int, dict[int, Deque[np.ndarray]]] = {}

    for cam_key in cameras.keys():
        for nn_key in config.keys():
            camera_buffers[cam_key] = {}
            camera_buffers[cam_key][nn_key] = deque(maxlen=int(config[nn_key].buffer_size))

    # Синхронно захватываем видео в процессе
    for key in cameras.keys():
        camera_gears[key] = ReconnectingRTSPGear(
            cam_address=cameras[key],
            reset_attempts=20,
            reset_delay=5,
            is_logging=True
        )

    stream_gears: dict[int, StreamGear] = {}

    #  Синхронно стримим на фронт
    if is_stream_enable:
        for key in cameras.keys():
            stream_params = {"-vf": "scale=1280:-2", "-profile:v": "high444", "-livestream": True, "-streams": [
                {"-resolution": "640x360"}]}
            stream_gears[key] = StreamGear(output=f"streams/hls{key}/cam{key}.m3u8", format="hls",
                                           logging=True, **stream_params)

    while True:
        is_error = False
        for cam_key in cameras.keys():
            frame = camera_gears[cam_key].read()
            if frame is None:
                is_error = True
                break
            for cnn_key in config.keys():

                preprocess_func = getattr(preprocess_frames_functions, config[cnn_key].preprocess_func_name,
                                          None)

                if preprocess_func is not None and not callable(preprocess_func):
                    raise TypeError('preprocess_func is not a function')

                frame = preprocess_func(frame)

                camera_buffers[cam_key][cnn_key].append(frame)

                if is_stream_enable:
                    reduce_frame = reducer(frame, percentage=50)
                    for key in stream_gears.keys():
                        stream_gears[key].stream(reduce_frame)

                if len(camera_buffers[cam_key][cnn_key]) == int(config[cnn_key].buffer_size):

                    try:
                        start_time_pred = datetime.now()
                        arr = np.array(camera_buffers[cam_key][cnn_key])
                        data = produce_file(arr)

                        prediction = prediction_request(config[cnn_key].url, data)

                        # producer.produce(
                        #     topic="violence_prediction",
                        #     value=prediction.json()['prediction'],
                        #     headers={
                        #         "cam_num": str.encode(str(key))
                        #     }
                        # )

                        print(prediction)
                        print("request bound time:", datetime.now() - start_time_pred)

                    finally:
                        camera_buffers[cam_key][cnn_key].clear()

        if is_error:
            break


def process(cameras: dict[int, str], config: dict[int, NeuroserviceConfig], is_stream_enable: bool):
    asyncio.run(start_stream(cameras, config, is_stream_enable))


if __name__ == '__main__':
    num_workers = cpu_count()

    need_streaming = False

    sources = [({1: "rtsp://cactus.tv:1554/cam15"}, {
        1: NeuroserviceConfig(url="http://localhost:8005/predict", buffer_size=64,
                              preprocess_func_name="preprocess_frame_violence")

    }, need_streaming)]

    with Pool(processes=num_workers) as pool:
        pool.starmap(process,
                     [s for s in sources])
