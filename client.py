import socket
import numpy as np
from scipy.interpolate import interp1d
import crepe
import select
from standard_pitch import predict_to_standard
import struct

debug = 1


#todo  return the biggest absolute value of the shifter_pitch of each ten batch when call to return the data.


def apply_pitch_shift(spectrogram, phase, pitch_shift_value, sample_rate, fft_frame_size):
    freq_per_bin = sample_rate / fft_frame_size
    shifted_spectrum = np.zeros(len(spectrogram), dtype=complex)

    for k in range(len(spectrogram)):
        original_freq = k * freq_per_bin
        shifted_freq = original_freq + pitch_shift_value

        new_bin = int(np.round(shifted_freq / freq_per_bin))

        if 0 <= new_bin < len(spectrogram):
            shifted_spectrum[new_bin] += spectrogram[k] * np.exp(1j * phase[k])

    return shifted_spectrum


def split_data_(data, fft_frame_size):
    if len(data) <= fft_frame_size:
        return [data]
    elif fft_frame_size < len(data) <= 2 * fft_frame_size:
        return [data[0:fft_frame_size], data[fft_frame_size:2:]]
    elif 2 * fft_frame_size < len(data) <= 3 * fft_frame_size:
        return [data[0: fft_frame_size], data[fft_frame_size: 2 * fft_frame_size], data[2 * fft_frame_size:]]


def tune_and_insert(window_data, processed_data, start_idx):
    fft_frame_size = 2048
    sample_rate = 48000
    window_size = 20
    time, frequency, confidence, activation = crepe.predict(
        window_data, sample_rate, "tiny", viterbi=True, step_size=10
    )
    pitch_shift = frequency - np.array([predict_to_standard(i) for i in frequency])
    split_data = split_data_(window_data, fft_frame_size)

    fft_result = [np.fft.fft(segment) for segment in split_data]
    spectrogram = [np.abs(i) for i in fft_result]
    phase = [np.angle(i) for i in fft_result]
    time_original = np.linspace(0, len(window_data) / sample_rate, len(pitch_shift))
    time_target = np.linspace(0, len(window_data) / sample_rate, len(split_data))

    interpolator = interp1d(time_original, pitch_shift, kind='cubic', fill_value="extrapolate")
    pitch_shift_interpolated = interpolator(time_target)

    shifted_fft = [
        apply_pitch_shift(spectrogram[i], phase[i], pitch_shift_interpolated[i], sample_rate, fft_frame_size)
        for i in range(len(spectrogram))
    ]
    output = np.zeros(len(window_data))
    current_position = 0  #

    for i, frame in enumerate(shifted_fft):
        time_domain = np.fft.ifft(frame).real
        frame_length = len(time_domain)
        end_position = min(current_position + frame_length, len(output))
        output[current_position:end_position] += time_domain[: end_position - current_position]
        current_position += frame_length
    split_output = np.array_split(output, window_size)
    for i, processed_segment in enumerate(split_output):
        if start_idx + i >= len(processed_data):
            processed_data.append(processed_segment)
        else:
            processed_data[start_idx + i] = processed_segment


def main():
    server_ip = '127.0.0.1'  # local address
    server_port = 14213  # todo determine hy's port
    window_size = 10
    data_queue = []  # our window size
    start_idx = 0
    return_data_list = []
    return_idx = 0
    piles_cnt = 0

    request_cnt = 0

    # some how we create a client

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    client_socket.setblocking(False)

    try:
        while True:
            # read all possible data
            # data = b''
            ready_to_read, _, _ = select.select([client_socket], [], [], 0.01)
            if ready_to_read:
                data = client_socket.recv(4096)
            else:
                # 超时或无数据，处理其他逻辑
                continue

            if len(data) == 0:
                continue

            first_byte = int.from_bytes(data[:1], byteorder='little')
            if first_byte == 1:
                pruned_data = data[1:]
                if len(data) < 4 * 479:
                    continue
                short_data = data[1:480*4+1]
                packet_data = np.frombuffer(short_data, dtype=np.float32)
                data_queue.append(packet_data)
                piles_cnt += 1
                if len(data_queue) >= window_size and piles_cnt >= 20:
                    windowed_data = np.concatenate(data_queue[start_idx:start_idx + window_size])
                    tune_and_insert(windowed_data, return_data_list, start_idx)
                    start_idx += 10
                    piles_cnt = 0

            elif first_byte == 2:
                if len(return_data_list) == 0 or len(data_queue) < window_size:
                    request_cnt += 1
                    continue
                if return_idx >= len(return_data_list):
                    continue
                return_data = return_data_list[return_idx]
                return_data = return_data.astype(np.float32)
                return_idx += 1
                data_to_send = return_data.tobytes()
                header = struct.pack('B', 3)
                data_with_header = header + data_to_send
                client_socket.send(data_with_header)

    finally:
        client_socket.close()


if __name__ == "__main__":
    main()
