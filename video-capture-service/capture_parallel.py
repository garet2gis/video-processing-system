from multiprocessing import Pool, cpu_count
import numpy as np
from typing import Deque, Any
from ReconnectingRTSPGear.ReconnectingRTSPGear import ReconnectingRTSPGear
from collections import deque
from datetime import datetime, timedelta
import requests
import configuration
from configuration import sources_config, NeuroserviceConfig
import io
import asyncio
import json
import threading
from confluent_kafka import Producer
import logging
from vidgear.gears import StreamGear
import os
from vidgear.gears.helper import reducer
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

TOPIC_NAME = os.getenv('TOPIC_NAME')
LOCALHOST = os.getenv('LOCALHOST')
# in docker env: KAFKA_INSTANCE_DOCKER
# in local env: KAFKA_INSTANCE
KAFKA_INSTANCE = os.getenv('KAFKA_INSTANCE')

config = {
    'bootstrap.servers': KAFKA_INSTANCE,
    'enable.idempotence': True,
    'acks': 'all',
    'retries': 100,
    'compression.type': 'snappy',
    'linger.ms': 5,
    'batch.num.messages': 32
}


def frames_to_file(frames: Any) -> dict[str, io.BytesIO]:
    bytes_image = frames.tobytes()
    stream = io.BytesIO(bytes_image)
    return {"file": stream}


def prediction_request(url: str, data: dict[str, io.BytesIO]) -> str:
    prediction = requests.post(url, files=data)
    return prediction.json()['prediction']


def predict(url: str, arr: np.ndarray, cam_key: int, date_time: datetime, producer: Optional[Producer] = None):
    data = frames_to_file(arr)

    prediction = prediction_request(url, data)
    print(prediction)
    data = {"prediction": prediction, "cam_id": cam_key, "timestamp_delay": date_time.timestamp()}
    if producer is not None:
        producer.produce(
            topic=TOPIC_NAME,
            value=json.dumps(data).encode("ascii"),
        )
        producer.poll(0)

    logging.info(f"io bound time: {datetime.now() - date_time}")


def is_timeout_end(start_time_loop: datetime, timeout_time: int) -> bool:
    return datetime.now() - start_time_loop > timedelta(seconds=float(timeout_time))


async def start_capturing(cameras: dict[int, str], neuroservices: dict[int, NeuroserviceConfig], need_streaming=False,
                          need_producing=False):
    # video capture gears
    camera_gears: dict[int, ReconnectingRTSPGear] = {}

    start_time_loop = datetime.now()

    # producer for communication with backend service
    if need_producing:
        producer = Producer(config)

    # camera buffers for every specific cam and neuroservice
    camera_buffers: dict[int, dict[int, Deque[np.ndarray]]] = {}
    for cam_key in cameras.keys():
        for nn_key in neuroservices.keys():
            camera_buffers[cam_key] = {}
            camera_buffers[cam_key][nn_key] = deque(maxlen=int(neuroservices[nn_key].buffer_size))

    stream_gears: dict[int, StreamGear] = {}
    if need_streaming:
        #  synchronously stream over the HLS protocol
        for cam_key in cameras.keys():
            stream_params = {"-livestream": True, "-input_framerate": 20}
            stream_gears[cam_key] = StreamGear(output=f"streams/hls{cam_key}/cam{cam_key}.m3u8", format="hls",
                                               logging=True, **stream_params)

    # synchronously capturing video
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
                # frame preprocessing function for this neural service
                preprocess_func = getattr(configuration,
                                          neuroservices[neuroservice_key].preprocess_func_name,
                                          None)

                if preprocess_func is not None and not callable(preprocess_func):
                    raise TypeError('preprocess_func is not a function')

                if need_streaming:
                    reduce_frame = reducer(frame, percentage=70)
                    for key in stream_gears.keys():
                        stream_gears[key].stream(reduce_frame)

                frame = preprocess_func(frame)

                #  if buffer is filled with required number of frames
                if len(camera_buffers[cam_key][neuroservice_key]) == int(
                        neuroservices[neuroservice_key].buffer_size) and \
                        is_timeout_end(start_time_loop, neuroservices[neuroservice_key].timeout):
                    try:
                        start_time_loop = datetime.now()

                        arr = np.array(camera_buffers[cam_key][neuroservice_key])

                        # do IO operations in a separate thread
                        if need_producing:
                            threading.Thread(target=predict, args=(
                                neuroservices[neuroservice_key].url, arr, cam_key, start_time_loop, producer,),
                                             daemon=True).start()
                        else:
                            threading.Thread(target=predict, args=(
                                neuroservices[neuroservice_key].url, arr, cam_key, start_time_loop, None,),
                                             daemon=True).start()

                    finally:
                        camera_buffers[cam_key][neuroservice_key].clear()
                elif is_timeout_end(start_time_loop, neuroservices[neuroservice_key].timeout):
                    camera_buffers[cam_key][neuroservice_key].append(frame)

        if is_error:
            producer.stop()
            for cam_key in cameras.keys():
                camera_gears[cam_key].stop()
                stream_gears[cam_key].terminate()
            break


def process(cameras: dict[int, str], config: dict[int, NeuroserviceConfig]):
    asyncio.run(start_capturing(cameras, config))


def create_paths(sources, protocol_stream_type='dash'):
    for t in sources:
        for d in t:
            for cam_id in d.keys():
                if os.path.exists(f'streams/{protocol_stream_type}{cam_id}'):
                    try:
                        os.rmdir(f'streams/{protocol_stream_type}{cam_id}')
                        os.mkdir(f'streams/{protocol_stream_type}{cam_id}')
                        logging.info(f'Made new directory to save stream: streams/{protocol_stream_type}{cam_id}')
                    except OSError:
                        logging.error('Unable to recreate directory')
                else:
                    try:
                        os.mkdir(f'streams/{protocol_stream_type}{cam_id}')
                        logging.info(f'Made new directory to save stream: streams/{protocol_stream_type}{cam_id}')
                    except OSError:
                        logging.error('Unable to create directory')


if __name__ == '__main__':
    num_workers = cpu_count()
    sources = sources_config
    create_paths(sources, 'hls')
    with Pool(processes=num_workers) as pool:
        pool.starmap(process,
                     [s for s in sources])
