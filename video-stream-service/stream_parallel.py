from multiprocessing import Pool, cpu_count
from ReconnectingRTSPGear.ReconnectingRTSPGear import ReconnectingRTSPGear
from vidgear.gears import StreamGear
from vidgear.gears.helper import reducer
import logging
import os

logging.basicConfig(level=logging.INFO)


def start_stream(cameras: dict[int, str]):
    camera_gears: dict[int, ReconnectingRTSPGear] = {}

    # Синхронно захватываем видео в процессе
    for key in cameras.keys():
        print(cameras[key])
        camera_gears[key] = ReconnectingRTSPGear(
            cam_address=cameras[key],
            reset_attempts=20,
            reset_delay=5,
            is_logging=True
        )

    stream_gears: dict[int, StreamGear] = {}

    #  Синхронно стримим на фронт
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

            reduce_frame = reducer(frame, percentage=50)
            for key in stream_gears.keys():
                stream_gears[key].stream(reduce_frame)

        if is_error:
            for cam_key in cameras.keys():
                camera_gears[cam_key].stop()
                stream_gears[cam_key].terminate()
            break


def process(cameras: dict[int, str]):
    start_stream(cameras)


if __name__ == '__main__':
    num_workers = cpu_count()

    # get this from database
    sources = [({1: "./test_violence_videos/violence2.mp4"},)]

    for t in sources:
        for d in t:
            for cam_id in d.keys():
                if os.path.exists(f'streams/hls{cam_id}'):
                    try:
                        os.rmdir(f'streams/hls{cam_id}')
                        os.mkdir(f'streams/hls{cam_id}')
                        logging.info(f'Made new directory to save stream: streams/hls{cam_id}')
                    except OSError:
                        logging.error('Unable to recreate directory')
                else:
                    try:
                        os.mkdir(f'streams/hls{cam_id}')
                        logging.info(f'Made new directory to save stream: streams/hls{cam_id}')
                    except OSError:
                        logging.error('Unable to create directory')

    with Pool(processes=num_workers) as pool:
        pool.starmap(process,
                     [s for s in sources])
