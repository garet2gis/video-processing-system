from vidgear.gears import CamGear, WriteGear, StreamGear
import cv2
from vidgear.gears.helper import reducer

# refactor
cameras = {
    1: "rtsp://cactus.tv:1554/cam50",
    2: "rtsp://cactus.tv:1554/cam15",
}

cam_gears = {}

for key, value in cameras.items():
    cam_gears[key] = CamGear(source=value, logging=True).start()

stream_params = {}

for key in cameras.keys():
    stream_params[key] = {"-input_framerate": cam_gears.get(key).framerate, "-livestream": True}

stream_gears = {}

for key in stream_params.keys():
    stream_gears[key] = StreamGear(output=f"streams/hls{key}/cam{key}.m3u8", format="hls",
                                   **stream_params.get(key))

# infinite loop
while True:
    is_error = False
    frames = {}
    for i in cam_gears.keys():
        frames[i] = cam_gears.get(i).read()
        if frames[i] is None:
            print(i)
            is_error = True
    if is_error:
        break

    # do smth with frames
    for i in frames.keys():
        frames[i] = reducer(frames[i], percentage=40)
        # predict on 64 frames in buffer
        frames[i] = cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)

    for i in frames.keys():
        stream_gears.get(i).stream(frames[i])
        # cv2.imshow(f"Output Frame{i}", frames[i])

    key = cv2.waitKey(1) & 0xFF
    # check for 'q' key-press
    if key == ord("q"):
        # if 'q' key-pressed break out
        break

# safely close both video streams
for i in cam_gears.keys():
    cam_gears[i].stop()

for i in stream_gears.keys():
    stream_gears[i].terminate()
