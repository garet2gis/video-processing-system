import numpy as np
import keras.layers as layers
import keras.models as models
import keras.applications.vgg19 as pretrained_model
from keras.optimizers import adam_v2
import h5py


def get_model(weights_path):
    num_classes = 2
    np.random.seed(1234)
    vgg19 = pretrained_model.VGG19
    base_model = vgg19(include_top=False, weights='imagenet', input_shape=(160, 160, 3))

    cnn = models.Sequential()
    cnn.add(base_model)
    cnn.add(layers.Flatten())
    model = models.Sequential()

    model.add(layers.TimeDistributed(cnn, input_shape=(30, 160, 160, 3)))
    model.add(layers.LSTM(30, return_sequences=True))

    model.add(layers.TimeDistributed(layers.Dense(90)))
    model.add(layers.Dropout(0.1))

    model.add(layers.GlobalAveragePooling1D())

    model.add(layers.Dense(512, activation='relu'))
    model.add(layers.Dropout(0.3))

    model.add(layers.Dense(num_classes, activation="sigmoid"))

    adam = adam_v2.Adam(learning_rate=0.0005, beta_1=0.9, beta_2=0.999, epsilon=1e-08)
    model.load_weights(weights_path)

    model.compile(loss='binary_crossentropy', optimizer=adam, metrics=["accuracy"])

    model.summary()

    return model


def reload_model_for_current_system():
    model = get_model('app/neural_networks/violence_detection_cnn_lstm/weights.h5')
    model.save('app/neural_networks/violence_detection_cnn_lstm/weights.h5')
