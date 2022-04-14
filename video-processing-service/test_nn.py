from keras.models import load_model
from video_transform.video_tranform import Video2Npy, load_data

model = load_model('models/weights.h5', compile=False)

video_violence = Video2Npy('./videos/violence.mp4')
video_not_violence = Video2Npy('./videos/not_violence.mp4')

frames_v = load_data(video_violence)
frames_nv = load_data(video_not_violence)

print("Вероятность насилия (+):", model.predict(frames_v)[0][0] * 100)
print("Вероятность насилия (-):", model.predict(frames_nv)[0][0] * 100)
