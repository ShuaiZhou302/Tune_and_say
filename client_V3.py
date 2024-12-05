import multiprocessing
from multiprocessing import Manager
import numpy as np
import socket
import select
import struct
from scipy.interpolate import interp1d
import crepe
from client import split_data_, apply_pitch_shift
from standard_pitch import predict_to_standard

# 定义处理音频数据的函数
def tune_and_insert(window_data, processed_data_queue):
    fft_frame_size = 8192
    sample_rate = 48000
    window_size = 40
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
    current_position = 0

    for i, frame in enumerate(shifted_fft):
        time_domain = np.fft.ifft(frame).real
        frame_length = len(time_domain)
        end_position = min(current_position + frame_length, len(output))
        output[current_position:end_position] += time_domain[: end_position - current_position]
        current_position += frame_length

    split_output = np.array_split(output, window_size)
    for processed_segment in split_output:
        processed_data_queue.put(processed_segment)

# 音频处理进程的目标函数
def audio_processing_process(data_queue, processed_data_queue):
    while True:
        windowed_size = 40
        while len(data_queue) != 0:
            if len(data_queue) >= windowed_size:
                windowed_data = np.concatenate(data_queue[0:windowed_size])
                del data_queue[0:windowed_size]
                tune_and_insert(windowed_data,processed_data_queue)
            else:
                break


# 主函数
def main():
    server_ip = '127.0.0.1'
    server_port = 14213
    window_size = 10
    manager = multiprocessing.Manager()
    data_queue = manager.list()
    processed_data_queue = multiprocessing.Queue()

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    client_socket.setblocking(False)

    # 创建音频处理进程
    audio_process = multiprocessing.Process(target=audio_processing_process, args=(data_queue, processed_data_queue))
    audio_process.start()

    try:
        while True:
            ready_to_read, _, _ = select.select([client_socket], [], [], 0.01)
            if ready_to_read:
                data = client_socket.recv(4096)
                if len(data) == 0:
                    continue

                first_byte = int.from_bytes(data[:1], byteorder='little')
                if first_byte == 1:
                    short_data = data[1:480*4+1]
                    packet_data = np.frombuffer(short_data, dtype=np.float32)
                    data_queue.append(packet_data)

                elif first_byte == 2:
                    if not processed_data_queue.empty():
                        return_data = processed_data_queue.get()
                        return_data = return_data.astype(np.float32)
                        data_to_send = return_data.tobytes()
                        header = struct.pack('B', 3)
                        data_with_header = header + data_to_send
                        client_socket.send(data_with_header)

    finally:
        client_socket.close()
        audio_process.terminate()  # 确保进程被终止

if __name__ == "__main__":
    main()
