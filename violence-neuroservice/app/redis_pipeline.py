import base64
import json
import time
from keras.models import load_model
import numpy as np
import redis
from dotenv import load_dotenv
from pathlib import Path
import os
from datetime import datetime
import logging
from neural_networks.video_transform import video_tranform

logging.basicConfig(level=logging.INFO)

dotenv_path = Path('../.env')

load_dotenv(dotenv_path)

# .env
BATCH_SIZE = os.getenv('BATCH_SIZE')
QUEUE_NAME = os.getenv('QUEUE_NAME')
TIMEOUT_MODEL = os.getenv('TIMEOUT_MODEL')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
MODEL_TYPE = os.getenv('MODEL_TYPE')

# Connect to Redis server
db = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)

if MODEL_TYPE == 'cnn3d':
    model = load_model("app/neural_networks/violence_detection_3dcnn/weights.h5", compile=False)
    shape = (1, 64, 224, 224, 3)
    np_dtype = np.uint8
elif MODEL_TYPE == 'cnn_lstm':
    model = load_model("app/neural_networks/violence_detection_cnn_lstm/weights.h5", compile=False)
    shape = (1, 30, 160, 160, 3)
    np_dtype = np.float64
else:
    model = load_model("app/neural_networks/mobile_net_pretrained/weights.h5", compile=False)
    shape = (1, 128, 128, 3)
    np_dtype = np.uint8


def base64_decode_frames(a, dtype: np.dtype, shape):
    a = bytes(a, encoding="utf-8")

    # Convert the string to a NumPy array using the supplied data
    # type and target shape
    a = np.frombuffer(base64.decodebytes(a), dtype=dtype)
    a = a.reshape(shape)

    # Return the decoded image
    return a


def classify_process():
    # Continually poll for new images to classify
    deserialize_bound_time = 0
    start = True

    while True:
        # Pop off multiple images from Redis queue atomically

        get_from_redis_bound_time = datetime.now()

        with db.pipeline() as pipe:
            pipe.lrange(QUEUE_NAME, 0, int(BATCH_SIZE) - 1)
            pipe.ltrim(QUEUE_NAME, BATCH_SIZE, -1)
            queue, _ = pipe.execute()

        if len(queue) > 0:
            logging.info(f"get frames bound time: {datetime.now() - get_from_redis_bound_time}")

        image_IDs = []
        batch = None

        if len(queue) > 0 and start:
            deserialize_bound_time = datetime.now()
            start = False

        for q in queue:

            # Deserialize the object and obtain the input image
            q = json.loads(q.decode("utf-8"))
            frames = base64_decode_frames(q["frames"],
                                          np_dtype,
                                          shape)

            if MODEL_TYPE == 'cnn3d':
                frames = video_tranform.process_frames(frames)

            # Check to see if the batch list is None
            if batch is None:
                batch = frames

            # Otherwise, stack the data
            else:
                batch = np.vstack([batch, frames])

            image_IDs.append(q["id"])

        if len(image_IDs) > 0 and deserialize_bound_time != 0:
            logging.info(f"desirialize frames bound time: {datetime.now() - deserialize_bound_time}")
            deserialize_bound_time = 0
            start = True

        if len(image_IDs) > 0:
            predict_bound_time = datetime.now()

            predictions = model.predict(batch)

            print(predictions)

            for (imageID, prediction) in zip(image_IDs, predictions):
                db.set(imageID, json.dumps({"prediction": float(prediction[1])}))

            logging.info(f"predict frames bound time: {datetime.now() - predict_bound_time}")

        # Sleep for a small amount
        time.sleep(float(TIMEOUT_MODEL))


if __name__ == "__main__":
    classify_process()
