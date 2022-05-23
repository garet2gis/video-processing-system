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
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)

TIMEOUT_SEC = os.getenv('TIMEOUT_SEC')
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


class зNeuroserviceConfig(BaseModel):
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


async def start_stream(cameras: dict[int, str], neuroservices: dict[int, NeuroserviceConfig], need_streaming=False,
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

        #  Синхронно стримим на фронт
        for cam_key in cameras.keys():
            stream_params = {"-livestream": True, "-input_framerate": 20}
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

                if need_streaming:
                    reduce_frame = reducer(frame, percentage=70)
                    for key in stream_gears.keys():
                        stream_gears[key].stream(reduce_frame)

                frame = preprocess_func(frame)

                #  если буффер заполнен необходимым количеством кадров
                if len(camera_buffers[cam_key][neuroservice_key]) == int(
                        neuroservices[neuroservice_key].buffer_size) and datetime.now() - start_time_loop > timedelta(
                    seconds=float(TIMEOUT_SEC)):
                    try:
                        start_time_loop = datetime.now()

                        arr = np.array(camera_buffers[cam_key][neuroservice_key])

                        # TODO: слидить за количеством потоков
                        # делаем операции ввода вывода в отдельном потоке
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


def create_paths(sources, type='dash'):
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
    sources = [({1: "rtsp://cactus.tv:1554/cam223"}, {
        1: NeuroserviceConfig(url=f"http://localhost:8005/predict_cnn_lstm", buffer_size=30,
                              preprocess_func_name="violence_preprocess_cnn_lstm")}),
               ({2: "rtsp://cactus.tv:1554/cam71"}, {
                   2: NeuroserviceConfig(url=f"http://localhost:8005/predict_frame", buffer_size=1,
                                         preprocess_func_name="violence_preprocess_v2")})]

    # }), ({3: "rtsp://cactus.tv:1554/cam169"}, {
    #     3: NeuroserviceConfig(url=f"http://134.0.117.96:8005/predict_frame", buffer_size=1,
    #                           preprocess_func_name="violence_preprocess_v2")
    # }), ({6: "rtsp://cactus.tv:1554/cam15"}, {
    #     6: NeuroserviceConfig(url=f"http://134.0.117.96:8005/predict_frame", buffer_size=1,
    #                           preprocess_func_name="violence_preprocess_v2")
    # }), ({5: "./test_violence_videos/fights_v2.mp4"}, {
    #     5: NeuroserviceConfig(url=f"http://134.0.117.96:8005/predict_frame", buffer_size=1,
    #                           preprocess_func_name="violence_preprocess_v2")
    # }), ({4: "./test_violence_videos/v_test.mp4"}, {
    #     4: NeuroserviceConfig(url=f"http://134.0.117.96:8005/predict_frame", buffer_size=1,
    #                           preprocess_func_name="violence_preprocess_v2")
    # })]

    create_paths(sources, 'hls')

    with Pool(processes=num_workers) as pool:
        pool.starmap(process,
                     [s for s in sources])
