from multiprocessing import Pool, cpu_count
import numpy as np
from typing import Deque, Any
from ReconnectingRTSPGear.ReconnectingRTSPGear import ReconnectingRTSPGear
from collections import deque
from datetime import datetime, timedelta
import requests
import preprocess_frames_functions
import io
from pydantic import BaseModel
import asyncio
import json
import threading
from confluent_kafka import Producer
import logging
from vidgear.gears import StreamGear
import os
from vidgear.gears.helper import reducer

logging.basicConfig(level=logging.INFO)

TOPIC_NAME = "prediction"

# in docker env: host.docker.internal
# in local env: 127.0.0.1
LOCALHOST = "127.0.0.1"

KAFKA_INSTANCE = f"{LOCALHOST}:9092"

config = {
    'bootstrap.servers': KAFKA_INSTANCE,
    'enable.idempotence': True,
    'acks': 'all',
    'retries': 100,
    'compression.type': 'snappy',
    'linger.ms': 5,
    'batch.num.messages': 32
}


class NeuroserviceConfig(BaseModel):
    url: str
    buffer_size: int
    preprocess_func_name: str


def frames_to_file(frames: Any) -> dict[str, io.BytesIO]:
    bytes_image = frames.tobytes()
    stream = io.BytesIO(bytes_image)
    return {"file": stream}


def prediction_request(url: str, data: dict[str, io.BytesIO]) -> str:
    prediction = requests.post(url, files=data)

    return prediction.json()['prediction']


def predict(url: str, arr: np.ndarray, cam_key: int, producer: Producer, date_time: datetime):
    data = frames_to_file(arr)

    prediction = prediction_request(url, data)
    print(prediction)
    data = {"prediction": prediction, "cam_id": cam_key, "timestamp_delay": date_time.timestamp()}
    producer.produce(
        topic=TOPIC_NAME,
        value=json.dumps(data).encode("ascii"),
    )

    producer.poll(0)

    logging.info(f"io bound time: {datetime.now() - date_time}")


async def start_stream(cameras: dict[int, str], neuroservices: dict[int, NeuroserviceConfig]):
    # video capture gears
    camera_gears: dict[int, ReconnectingRTSPGear] = {}

    start_time_loop = datetime.now()

    # producer for communication with backend service
    producer = Producer(config)

    # camera buffers for every specific cam and neuroservice
    camera_buffers: dict[int, dict[int, Deque[np.ndarray]]] = {}
    for cam_key in cameras.keys():
        for nn_key in neuroservices.keys():
            camera_buffers[cam_key] = {}
            camera_buffers[cam_key][nn_key] = deque(maxlen=int(neuroservices[nn_key].buffer_size))

    stream_gears: dict[int, StreamGear] = {}

    #  Синхронно стримим на фронт
    for cam_key in cameras.keys():
        stream_params = {"-livestream": True}
        stream_gears[cam_key] = StreamGear(output=f"streams/hls{cam_key}/cam{cam_key}.m3u8", format="hls",
                                           logging=True, **stream_params)

    # синхронно захватываем видео
    for key in cameras.keys():
        camera_gears[key] = ReconnectingRTSPGear(
            cam_address=cameras[key],
            reset_attempts=20,
            reset_delay=5,
            is_logging=True
        )

    while True:
        is_error = False
        for cam_key in cameras.keys():
            frame = camera_gears[cam_key].read()
            if frame is None:
                is_error = True
                break

            for neuroservice_key in neuroservices.keys():
                # функция препроцессинга кадра для данного нейросервиса
                preprocess_func = getattr(preprocess_frames_functions,
                                          neuroservices[neuroservice_key].preprocess_func_name,
                                          None)

                if preprocess_func is not None and not callable(preprocess_func):
                    raise TypeError('preprocess_func is not a function')

                reduce_frame = reducer(frame, percentage=70)
                for key in stream_gears.keys():
                    stream_gears[key].stream(reduce_frame)

                frame = preprocess_func(frame)

                #  если буффер заполнен необходимым количеством кадров
                if len(camera_buffers[cam_key][neuroservice_key]) == int(
                        neuroservices[neuroservice_key].buffer_size) and datetime.now() - start_time_loop > timedelta(
                    seconds=0.7):
                    try:
                        start_time_loop = datetime.now()

                        arr = np.array(camera_buffers[cam_key][neuroservice_key])

                        # TODO: слидить за количеством потоков
                        # делаем операции ввода вывода в отдельном потоке
                        threading.Thread(target=predict, args=(
                            neuroservices[neuroservice_key].url, arr, cam_key, producer, start_time_loop,),
                                         daemon=True).start()

                    finally:
                        camera_buffers[cam_key][neuroservice_key].clear()
                else:
                    camera_buffers[cam_key][neuroservice_key].append(frame)

        if is_error:
            producer.stop()
            for cam_key in cameras.keys():
                camera_gears[cam_key].stop()
                stream_gears[cam_key].terminate()
            break


def process(cameras: dict[int, str], config: dict[int, NeuroserviceConfig]):
    asyncio.run(start_stream(cameras, config))


def create_pathes(sources, type='dash'):
    for t in sources:
        for d in t:
            for cam_id in d.keys():
                if os.path.exists(f'streams/{type}{cam_id}'):
                    try:
                        os.rmdir(f'streams/{type}{cam_id}')
                        os.mkdir(f'streams/{type}{cam_id}')
                        logging.info(f'Made new directory to save stream: streams/{type}{cam_id}')
                    except OSError:
                        logging.error('Unable to recreate directory')
                else:
                    try:
                        os.mkdir(f'streams/{type}{cam_id}')
                        logging.info(f'Made new directory to save stream: streams/{type}{cam_id}')
                    except OSError:
                        logging.error('Unable to create directory')


if __name__ == '__main__':
    num_workers = cpu_count()

    # get this from database
    sources = [({1: "./test_violence_videos/violence2.mp4"}, {
        1: NeuroserviceConfig(url=f"http://localhost:8005/predict_frame", buffer_size=1,
                              preprocess_func_name="violence_preprocess_v2")
    }), ({2: "rtsp://cactus.tv:1554/cam50"}, {
        2: NeuroserviceConfig(url=f"http://localhost:8005/predict_frame", buffer_size=1,
                              preprocess_func_name="violence_preprocess_v2")
    })]

    create_pathes(sources, 'hls')

    with Pool(processes=num_workers) as pool:
        pool.starmap(process,
                     [s for s in sources])
