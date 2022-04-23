from keras.models import Input, Model
from keras.layers import Dense, Flatten, Conv3D, MaxPooling3D, Dropout, Multiply
from keras.layers.core import Lambda
import h5py


# extract the rgb images
def get_rgb(input_x):
    rgb = input_x[..., :3]
    return rgb


# extract the optical flows
def get_opt(input_x):
    opt = input_x[..., 3:5]
    return opt


inputs = Input(shape=(64, 224, 224, 5))

rgb = Lambda(get_rgb, output_shape=None)(inputs)
opt = Lambda(get_opt, output_shape=None)(inputs)

rgb = Conv3D(
    16, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    rgb)
rgb = Conv3D(
    16, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    rgb)
rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)

rgb = Conv3D(
    16, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    rgb)
rgb = Conv3D(
    16, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    rgb)
rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)

rgb = Conv3D(
    32, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    rgb)
rgb = Conv3D(
    32, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    rgb)
rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)

rgb = Conv3D(
    32, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    rgb)
rgb = Conv3D(
    32, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    rgb)
rgb = MaxPooling3D(pool_size=(1, 2, 2))(rgb)

opt = Conv3D(
    16, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    opt)
opt = Conv3D(
    16, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    opt)
opt = MaxPooling3D(pool_size=(1, 2, 2))(opt)

opt = Conv3D(
    16, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    opt)
opt = Conv3D(
    16, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    opt)
opt = MaxPooling3D(pool_size=(1, 2, 2))(opt)

opt = Conv3D(
    32, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    opt)
opt = Conv3D(
    32, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(
    opt)
opt = MaxPooling3D(pool_size=(1, 2, 2))(opt)

opt = Conv3D(
    32, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='sigmoid', padding='same')(
    opt)
opt = Conv3D(
    32, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='sigmoid', padding='same')(
    opt)
opt = MaxPooling3D(pool_size=(1, 2, 2))(opt)

x = Multiply()([rgb, opt])
x = MaxPooling3D(pool_size=(8, 1, 1))(x)

x = Conv3D(
    64, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(x)
x = Conv3D(
    64, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(x)
x = MaxPooling3D(pool_size=(2, 2, 2))(x)

x = Conv3D(
    64, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(x)
x = Conv3D(
    64, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(x)
x = MaxPooling3D(pool_size=(2, 2, 2))(x)

x = Conv3D(
    128, kernel_size=(1, 3, 3), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(x)
x = Conv3D(
    128, kernel_size=(3, 1, 1), strides=(1, 1, 1), kernel_initializer='he_normal', activation='relu', padding='same')(x)
x = MaxPooling3D(pool_size=(2, 3, 3))(x)

x = Flatten()(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.2)(x)
x = Dense(32, activation='relu')(x)

# Build the model
pred = Dense(2, activation='softmax')(x)
model = Model(inputs=inputs, outputs=pred)
model.summary()

model.load_weights('./weights.h5')
