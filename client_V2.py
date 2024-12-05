import threading
import queue
import time
from scipy.interpolate import interp1d
import crepe
import numpy as np
import socket
import select
import struct
from client import split_data_,apply_pitch_shift

from standard_pitch import predict_to_standard

#global return data queue
# data_queue = []
data_queue = []
processed_data_queue = queue.Queue()

def audio_processing_thread():
    global data_queue
    window_size = 5
    while True:
        # if len(data_queue) >= 10:
        #     windowed_data = np.concatenate(data_queue[0:10])
        #     del data_queue[0:10]
        #     tune_and_insert(windowed_data)
        while len(data_queue) < window_size:
            time.sleep(0.005)

        while len(data_queue) != 0:
            if len(data_queue) >= window_size:
                windowed_data = np.concatenate(data_queue[0:window_size])
                del data_queue[0:window_size]
                tune_and_insert(windowed_data)
            else:
                break

def tune_and_insert(window_data):
    fft_frame_size = 1024
    sample_rate = 48000
    window_size = 5
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
    for i, processed_segment in enumerate(split_output):
        processed_data_queue.put(processed_segment)

def main():
    server_ip = '127.0.0.1'
    server_port = 14213


    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    client_socket.setblocking(False)

    # pitch thread
    threading.Thread(target=audio_processing_thread).start()

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
                    if (len(short_data) != 480 * 4):
                        print(f"Error length is {len(short_data)}")
                        continue
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

if __name__ == "__main__":
    main()
