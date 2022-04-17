from vidgear.gears import NetGear
from collections import deque
from keras.models import load_model
from video_transform.video_tranform import process_frames
import logging
import asyncio
import websockets
import json
from datetime import datetime
import concurrent.futures
from multiprocessing import Process


def prediction(model, frames):
    ret_val = model.predict(frames)
    return ret_val


class MultipleProcessing:
    def __init__(self):
        self.model = load_model('models/weights.h5', compile=False)
        options = {"bidirectional_mode": True}
        self.client = NetGear(receive_mode=True, logging=True, **options)
        self.cameras_buffers = {}
        self.connections = set()
        self.count = 0

    async def websocket_handler(self, websocket):
        self.connections.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.connections.remove(websocket)

    async def start_consuming(self):
        while True:
            data = self.client.recv()
            if data is None:
                break

            cam_num, frame = data

            cam_num = int(cam_num)

            if self.cameras_buffers.get(cam_num) is None:
                self.cameras_buffers[cam_num] = deque(maxlen=64)

            self.cameras_buffers[cam_num].append(frame)

            # logging.warning(f"cam: {cam_num} len: {len(self.cameras_buffers[cam_num])}")

            if len(self.cameras_buffers[cam_num]) == 64:
                print(f"{self.count} {str(datetime.now().strftime('%H:%M:%S'))}")

                # TODO: optimize this
                frames_64 = process_frames(self.cameras_buffers[cam_num])
                res = self.model.predict(frames_64)

                # logging.warning(f"cam: {cam_num} prediction: {res[0]}")

                event = {
                    "type": "prediction",
                    "cam_id": str(cam_num),
                    "is_violence": str(res[0][0]),
                    "time": str(datetime.now().strftime("%H:%M:%S")),
                    "count": str(self.count)
                }

                self.count += 1

                websockets.broadcast(self.connections, json.dumps(event))

                self.cameras_buffers[cam_num].clear()

            await asyncio.sleep(0)

        self.client.close()


async def main(streams):
    async with websockets.serve(streams.websocket_handler, "", 8010):
        await streams.start_consuming()


if __name__ == '__main__':
    multiple_streams = MultipleProcessing()
    asyncio.run(main(multiple_streams))
