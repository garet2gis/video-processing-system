# Integration custom neuroservices instruction

In configuration.py you can configure the capture service

You need to describe list of tuples with fields:
1. rtsp-url - connection link to the ip-camera
2. neuroservice config

Neuroservice config consists of the fields:
1. url - link to endpoint to send http-request to
2. buffer-size - number of frames to send
3. timeout - delay with which to send frames
4. preprocess_func_name - name of the preprocessing function

Also, you need to write preprocess_function if necessary.
This is a function that takes a frame, processes it (changes the resolution, normalizes) and returns it