# Integration custom neuroservices instruction

In configuration.py you can configure the capture service

You need to describe list of tuples with fields:
1. rtsp-url - connection link to the ip-camera
2. neuroservice config
3. id - unique camera id for identification

Neuroservice config consists of the fields:
1. url - link to endpoint to send http-request to
2. buffer-size - number of frames to send
3. timeout - delay with which to send frames
4. preprocess_func_name - name of the preprocessing function

Also, you need to write preprocess_function if necessary.
This is a function that takes a frame as np.array, processes it (changes the resolution or/and normalizes) and returns it


Exapmle of custom configuration:
```
sources_config = [({1: "rtsp://sorce_to_ip_camera"},
                   {1: NeuroserviceConfig(url="http://source_to_neuroservice_endpoint", buffer_size=15,
                                          preprocess_func_name="example_preprocess_frame", timeout=1)})]

def example_preprocess_frame(frame: np.ndarray) -> np.ndarray:
    # resize frame
    new_frame = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
    # normilize frame
    if np.max(new_frame) > 1:
        new_frame = new_frame / 255.0
    return new_frame
```
