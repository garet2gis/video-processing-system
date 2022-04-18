from typing import Optional
from fastapi import FastAPI
from keras.models import load_model
import os
import sys
from fastapi import FastAPI, File, HTTPException
from starlette.requests import Request
import numpy as np
import io
import zlib
from pydantic import BaseModel
import base64
from video_transform.video_tranform import process_frames
import pickle
import codecs

import uvicorn

app = FastAPI()

model = load_model("models/weights.h5", compile=False)


def uncompress_nparr(bytestring):
    """
    """
    return np.load(io.BytesIO(zlib.decompress(bytestring)))


@app.get("/")
def read_root():
    return {"Hello": "World"}


class Item(BaseModel):
    arr: list


class Prediction(BaseModel):
    success: bool
    prediction: float


@app.post("/predict", response_model=Prediction)
def test(request: Request, file: Item):
    data = {"success": False, "prediction": -1}
    if request.method == "POST":
        frames = np.array(file.arr)
        processed_frames = process_frames(frames)
        is_violence = float(model.predict(processed_frames)[0][0])
        data['prediction'] = is_violence
        data['success'] = True

    return data


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8005, reload=True)
