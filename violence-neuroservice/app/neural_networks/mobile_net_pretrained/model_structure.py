from keras.layers import Input
from keras.models import Model
from keras.layers.core import Dense
from keras.applications.mobilenet_v2 import MobileNetV2


def get_model():
    input_tensor = Input(shape=(128, 128, 3))
    base_model = MobileNetV2(pooling='avg',
                             include_top=False,
                             input_tensor=input_tensor)

    head_model = base_model.output
    head_model = Dense(1, activation="sigmoid")(head_model)
    model = Model(inputs=base_model.input, outputs=head_model)

    for layer in base_model.layers:
        layer.trainable = False

    model.compile(loss="binary_crossentropy",
                  optimizer='adam',
                  metrics=["accuracy"])

    return model


def reload_model_for_current_system():
    model = get_model()
    model.load_weights('./weights.h5')
    model.save('./weights.h5')
