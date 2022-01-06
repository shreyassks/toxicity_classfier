import matplotlib.pyplot as plt
import numpy as np

import tensorflow as tf
from keras.layers import Dense, Input, LSTM, Dropout, Bidirectional
from keras.layers import GlobalMaxPool1D, Embedding
from keras.models import Model
from keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
from config import *
from data_preprocess import data_preprocess
import yaml


params1 = yaml.safe_load(open("params.yaml"))["data-preprocess"]
vocab_size = params1["vocab_size"]
max_seq_length = params1["sequence_len"]
embedding_dim = params1["embedding_dim"]

params2 = yaml.safe_load(open("params.yaml"))["model-training"]
batch_size = params2["batch_size"]
epochs = params2["epochs"]
val_split = params2["val_split"]
# -------------------------------------------------------------------------
# class_weight = {0: 0.1590, 1: 1.4905, 2: 2.6980, 3: 2.8939, 4: 14.2920, 5: 16.2248, 6: 47.69}


def build_lstm_model(data, target_classes, embeddings, word_index):
    inp = Input(shape=(max_seq_length,), dtype='int32')
    embedded_sequences = Embedding(word_index+1, embedding_dim, weights=[embeddings],
                                   input_length=max_seq_length,
                                   trainable=False,
                                   name='embeddings')(inp)
    x = Bidirectional(LSTM(40, return_sequences=True, name='bilstm_layer'))(embedded_sequences)
    x = GlobalMaxPool1D()(x)
    x = Dropout(0.1)(x)
    x = Dense(20, activation="relu", kernel_initializer='he_uniform')(x)
    x = Dropout(0.1)(x)
    outs = Dense(7, activation="sigmoid", kernel_initializer='glorot_uniform')(x)
    # -------------------------------------------------------------------------
    model = Model(inputs=inp, outputs=outs)
    model.compile(loss='binary_crossentropy',
                  optimizer=Adam(),
                  metrics=[tf.keras.metrics.AUC()])
    # -------------------------------------------------------------------------
    model.summary()
    # -------------------------------------------------------------------------
    early_stopping = EarlyStopping(monitor='val_loss', verbose=1, patience=3, restore_best_weights=True)
    # -------------------------------------------------------------------------
    history = model.fit(data,
                        target_classes,
                        batch_size=batch_size,
                        epochs=epochs,
                        validation_split=val_split,
                        callbacks=[early_stopping],
                        verbose=1)
    # -------------------------------------------------------------------------
    model.save(MODEL_LOCATION)
    # -------------------------------------------------------------------------
    return model, history


# -------------------------------------------------------------------------
def plot_training_history(history):
    # "Accuracy"
    plt.plot(history.history['auc'])
    plt.plot(history.history['val_auc'])
    plt.title('AUC ROC Curve')
    plt.ylabel('AUC')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'], loc='upper left')
    plt.savefig('auc.jpg')

    # "Loss"
    plt.plot(history.history['loss'])
    plt.plot(history.history['val_loss'])
    plt.title('Model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'validation'], loc='upper left')
    plt.savefig('loss.jpg')


def execute():
    x_train = np.load("data/processed_data/x_train.npy", allow_pickle=True)
    ind, data = data_preprocess(x_train)
    target_classes = np.load("data/processed_data/y_train.npy")
    embeddings = np.load("data/embedding_matrix.npy")

    lstm_model, history = build_lstm_model(data, target_classes, embeddings, ind)
    plot_training_history(history)


# -------------------------------------------------------------------------
if __name__ == '__main__':
    execute()
