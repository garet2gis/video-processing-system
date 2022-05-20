import io


def frames_to_file(frames):
    bytes_image = frames.tobytes()
    stream = io.BytesIO(bytes_image)
    return {"file": stream}
