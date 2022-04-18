import asyncio
from multiprocessing import Pool, cpu_count
import sys
import cv2
import numpy as np
from typing import Dict, List, Deque
from ReconnectingRTSPGear.ReconnectingRTSPGear import ReconnectingRTSPGear
from vidgear.gears import StreamGear
from vidgear.gears.helper import reducer
from collections import deque
from datetime import datetime
import requests
import io
import aiohttp
import base64
import zlib
import pickle
import codecs
import logging


async def request(arr: np.array):
    async with aiohttp.ClientSession() as session:
        pokemon_url = 'http://localhost:8888/predict'
        async with session.post(pokemon_url, ) as resp:
            pokemon = await resp.json()
            print(pokemon['name'])


async def start_stream(cameras: Dict[int, str], is_stream_enable: bool):
    camera_gears: Dict[int, ReconnectingRTSPGear] = {}

    camera_buffers: Dict[int, Deque[np.array]] = {}

    for key in cameras.keys():
        camera_buffers[key] = deque(maxlen=64)

    #  Синхронно захватываем видео в процессе
    for key in cameras.keys():
        camera_gears[key] = ReconnectingRTSPGear(
            cam_address=cameras[key],
            reset_attempts=20,
            reset_delay=5,
            is_logging=True
        )

    stream_gears: Dict[int, StreamGear] = {}

    #  Синхронно стримим
    if is_stream_enable:
        for key in cameras.keys():
            stream_params = {"-vf": "scale=1280:-2", "-profile:v": "high444", "-livestream": True, "-streams": [
                {"-resolution": "640x360"}]}
            stream_gears[key] = StreamGear(output=f"streams/hls{key}/cam{key}.m3u8", format="hls",
                                           logging=True, **stream_params)
    while True:
        is_error = False
        for key in cameras.keys():
            frame = camera_gears[key].read()

            if (len(camera_buffers[key]) == 64):
                start_time = datetime.now()
                arr = np.array(camera_buffers[key])

                data = {'arr': arr.tolist()}

                prediction = requests.post("http://127.0.0.1:8005/predict", json=data)

                print(prediction.json()['prediction'])

                camera_buffers[key].clear()
                print(datetime.now() - start_time)

            if frame is None:
                is_error = True
                break

            if is_stream_enable:
                reduce_frame = reducer(frame, percentage=30)
                stream_gears[key].stream(reduce_frame)

            # resize frame for cnn
            frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = np.reshape(frame, (224, 224, 3))

            camera_buffers[key].append(frame)

        if is_error:
            break


def process(cameras: Dict[int, str], is_stream_enable: bool):
    asyncio.run(start_stream(cameras, is_stream_enable))


if __name__ == '__main__':
    num_workers = cpu_count()

    print(num_workers)

    with Pool(processes=num_workers) as pool:
        pool.starmap(process,
                     [({4: "rtsp://cactus.tv:1554/cam15"}, True)])
    # with Pool(processes=num_workers) as pool:
    #     pool.starmap(process,
    #                  [({4: "rtsp://cactus.tv:1554/cam15"}, True), ({1: "rtsp://cactus.tv:1554/cam1"}, True)])
