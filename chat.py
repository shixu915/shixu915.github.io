import tensorflow as tf
import numpy as np
import os

def load_data(filename):
    # 加载数据源并处理成输入和目标输出文本
    input_texts, target_texts = [], []
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.read().strip().split("\n")
    for line in lines:
        parts = line.split("\t")
        if len(parts) == 2:
            input_text, target_text = parts
            input_texts.append(input_text)
            target_texts.append(target_text)
    return input_texts, target_texts

def preprocess_data(input_texts, target_texts):
    # 对输入和目标输出文本进行编码和填充
    input_chars = set("".join(input_texts))
    target_chars = set("".join(target_texts))
    all_chars = sorted(list(input_chars | target_chars))
    num_encoder_tokens = len(input_chars)
    num_decoder_tokens = len(target_chars)
    max_encoder_seq_length = max([len(txt) for txt in input_texts if txt])
    max_decoder_seq_length = max([len(txt) for txt in target_texts if txt])

    input_token_index = dict([(char, i) for i, char in enumerate(all_chars)])
    target_token_index = dict([(char, i) for i, char in enumerate(all_chars)])

    encoder_input_data = []
    decoder_input_data = []
    decoder_target_data = []

    for i, (input_text, target_text) in enumerate(zip(input_texts, target_texts)):
        if not input_text or not target_text:
            continue
        encoder_input = np.zeros((max_encoder_seq_length, num_encoder_tokens), dtype="float32")
        for t, char in enumerate(input_text):
            encoder_input[t, input_token_index[char]] = 1.0
        decoder_input = np.zeros((max_decoder_seq_length, num_decoder_tokens), dtype="float32")
        for t, char in enumerate(target_text):
            decoder_input[t, target_token_index[char]] = 1.0
        decoder_target = np.zeros((max_decoder_seq_length, num_decoder_tokens), dtype="float32")
        for t, char in enumerate(target_text[1:]):
            decoder_target[t, target_token_index[char]] = 1.0
        encoder_input_data.append(encoder_input)
        decoder_input_data.append(decoder_input)
        decoder_target_data.append(decoder_target)

    encoder_input_data = np.array(encoder_input_data)
    decoder_input_data = np.array(decoder_input_data)
    decoder_target_data = np.array(decoder_target_data)

    return encoder_input_data, decoder_input_data, decoder_target_data, all_chars, input_token_index, target_token_index

def create_model(num_encoder_tokens, num_decoder_tokens, max_encoder_seq_length, max_decoder_seq_length):
    # 构建编码器-解码器模型
    encoder_inputs = tf.keras.layers.Input(shape=(None, num_encoder_tokens))
    decoder_inputs = tf.keras.layers.Input(shape=(None, num_decoder_tokens))
    encoder = tf.keras.layers.LSTM(256, return_state=True)
    encoder_outputs, state_h, state_c = encoder(encoder_inputs)
    encoder_states = [state_h, state_c]
    decoder_lstm = tf.keras.layers.LSTM(256, return_sequences=True, return_state=True)
    decoder_outputs, _, _ = decoder_lstm(decoder_inputs, initial_state=encoder_states)
    decoder_dense = tf.keras.layers.Dense(num_decoder_tokens, activation="softmax")
    decoder_outputs = decoder_dense(decoder_outputs)
    model = tf.keras.models.Model([encoder_inputs, decoder_inputs], decoder_outputs)
    model.compile(optimizer="rmsprop", loss="categorical_crossentropy")
    return model

def train_model(model, encoder_input_data, decoder_input_data, decoder_target_data):
    # 训练模型
    model.fit(
        [encoder_input_data, decoder_input_data],
        decoder_target_data,
        batch_size=64,
        epochs=50,
        validation_split=0.2
    )

def predict(model, input_text, all_chars, input_token_index, target_token_index, max_decoder_seq_length):
    # 使用训练好的模型进行预测
    states_value = model.layers[0].states
    encoder_model = tf.keras.models.Model(model.input[0], states_value)
    decoder_state_input_h = tf.keras.layers.Input(shape=(256,))
    decoder_state_input_c = tf.keras.layers.Input(shape=(256,))
    decoder_states_inputs = [decoder_state_input_h, decoder_state_input_c]
    decoder_lstm = model.layers[3]
    decoder_outputs, state_h, state_c = decoder_lstm(model.input[1], initial_state=decoder_states_inputs)
    decoder_states = [state_h, state_c]
    decoder_dense = model.layers[4]
    decoder_outputs = decoder_dense(decoder_outputs)
    decoder_model = tf.keras.models.Model([model.input[1]] + decoder_states_inputs, [decoder_outputs] + decoder_states)
    input_seq = np.zeros((1, len(input_text), len(all_chars)), dtype="float32")
    for t, char in enumerate(input_text):
        input_seq[0, t, input_token_index[char]] = 1.0
    states_value = encoder_model.predict(input_seq)
    target_seq = np.zeros((1, 1, len(all_chars)), dtype="float32")
    target_seq[0, 0, target_token_index["\t"]] = 1.0
    output_text = ""
    stop_condition = False
    while not stop_condition:
        output_tokens, h, c = decoder_model.predict([target_seq] + states_value)
        sampled_token_index = np.argmax(output_tokens[0, -1, :])
        sampled_char = all_chars[sampled_token_index]
        output_text += sampled_char
        if (sampled_char == "\n" or len(output_text) >= max_decoder_seq_length):
            stop_condition = True
        target_seq = np.zeros((1, 1, len(all_chars)), dtype="float32")
        target_seq[0, 0, sampled_token_index] = 1.0
        states_value = [h, c]
    return output_text

if __name__ == "__main__":
    # 设置超参数
    filename = "hutao.txt"
    batch_size = 64
    epochs = 50
    
    # 加载数据源
    input_texts, target_texts = load_data(filename)
    
    # 对数据进行预处理
    encoder_input_data, decoder_input_data, decoder_target_data, all_chars, input_token_index, target_token_index = preprocess_data(input_texts, target_texts)
    num_encoder_tokens = len(input_token_index)
    num_decoder_tokens = len(target_token_index)
    max_encoder_seq_length = encoder_input_data.shape[1]
    max_decoder_seq_length = decoder_input_data.shape[1]
    
    # 构建模型
    model = create_model(num_encoder_tokens, num_decoder_tokens, max_encoder_seq_length, max_decoder_seq_length)
    
    # 训练模型
    train_model(model, encoder_input_data, decoder_input_data, decoder_target_data)
    
    # 使用模型进行预测
    input_text = "我喜欢胡桃"
    output_text = predict(model, input_text, all_chars, input_token_index, target_token_index, max_decoder_seq_length)
    print("输入：", input_text)
    print("输出：", output_text)
