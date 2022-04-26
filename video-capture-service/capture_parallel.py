from multiprocessing import Pool, cpu_count
import numpy as np
from typing import Deque, Any
from ReconnectingRTSPGear.ReconnectingRTSPGear import ReconnectingRTSPGear
from collections import deque
from datetime import datetime
import requests
import preprocess_frames_functions
import io
from pydantic import BaseModel
import asyncio
import json
import threading
from confluent_kafka import Producer
import logging

logging.basicConfig(level=logging.INFO)

TOPIC_NAME = "prediction"

# in docker env: host.docker.internal
# in local env: 127.0.0.1
LOCALHOST = "host.docker.internal"

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


def predict(url: str, arr: np.ndarray, cam_key: int, producer: Producer):
    date_time = datetime.now()

    data = frames_to_file(arr)

    prediction = prediction_request(url, data)
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

    # producer for communication with backend service
    producer = Producer(config)

    # camera buffers for every specific cam and neuroservice
    camera_buffers: dict[int, dict[int, Deque[np.ndarray]]] = {}
    for cam_key in cameras.keys():
        for nn_key in neuroservices.keys():
            camera_buffers[cam_key] = {}
            camera_buffers[cam_key][nn_key] = deque(maxlen=int(neuroservices[nn_key].buffer_size))

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

                frame = preprocess_func(frame)

                camera_buffers[cam_key][neuroservice_key].append(frame)

                #  если буффер заполнен необходимым количеством кадров
                if len(camera_buffers[cam_key][neuroservice_key]) == int(neuroservices[neuroservice_key].buffer_size):
                    try:
                        arr = np.array(camera_buffers[cam_key][neuroservice_key])

                        # TODO: слидить за количеством потоков
                        # делаем операции ввода вывода в отдельном потоке
                        th = threading.Thread(target=predict, args=(
                            neuroservices[neuroservice_key].url, arr, cam_key, producer,), daemon=True)
                        th.start()

                    finally:
                        camera_buffers[cam_key][neuroservice_key].clear()

        if is_error:
            producer.stop()
            for cam_key in cameras.keys():
                camera_gears[cam_key].stop()
            break


def process(cameras: dict[int, str], config: dict[int, NeuroserviceConfig]):
    asyncio.run(start_stream(cameras, config))


if __name__ == '__main__':
    num_workers = cpu_count()

    # get this from database
    sources = [({1: "./test_violence_videos/violence2.mp4"}, {
        1: NeuroserviceConfig(url=f"http://{LOCALHOST}:8005/predict", buffer_size=64,
                              preprocess_func_name="violence_preprocess")
    })]

    with Pool(processes=num_workers) as pool:
        pool.starmap(process,
                     [s for s in sources])
