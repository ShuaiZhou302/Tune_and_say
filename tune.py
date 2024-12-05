import numpy as np
from scipy.interpolate import interp1d
from scipy.io import wavfile
from standard_pitch import predict_to_standard
import crepe
from scipy.signal import resample


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
        return [data[0 : fft_frame_size],data[fft_frame_size: 2*fft_frame_size],data[2*fft_frame_size:]]

"""
window
"""
# def split_data_(data, fft_frame_size):
#     if len(data) <= fft_frame_size:
#         window = np.hanning(len(data))
#         return [data * window],window
#     elif fft_frame_size < len(data) <= 2 * fft_frame_size:
#         window1 = np.hanning(fft_frame_size)
#         window2 = np.hanning(len(data) - fft_frame_size)
#         return [data[0:fft_frame_size]*window1, data[fft_frame_size:2:]*window2],np.concatenate([window1,window2])
#     elif 2 * fft_frame_size < len(data) <= 3 * fft_frame_size:
#         window1 = np.hanning(fft_frame_size)
#         window2 = np.hanning(fft_frame_size)
#         window3 = np.hanning(len(data) - 2 * fft_frame_size)
#         return [data[0 : fft_frame_size]*window1,data[fft_frame_size: 2*fft_frame_size]*window2,data[2*fft_frame_size:]*window3],np.concatenate([window1,window2,window3])



def tune(data, sample_rate):
    batch_size = 480
    window_size = 10
    fft_frame_size = 2048

    num_batches = int(np.ceil(len(data) / batch_size))
    data_list = np.array_split(data, num_batches)

    processed_data = [np.zeros_like(batch) for batch in data_list]
    for start_idx in range(len(data_list) - window_size + 1):
        window_data = np.concatenate(data_list[start_idx : start_idx + window_size])

        time, frequency, confidence, activation = crepe.predict(
            window_data, sample_rate, "tiny", viterbi=True, step_size=10
        )
        pitch_shift = frequency - np.array([predict_to_standard(i) for i in frequency])
        split_data= split_data_(window_data, fft_frame_size)


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
        output = output
        split_output = np.array_split(output, window_size)
        for i, processed_segment in enumerate(split_output):
            processed_data[start_idx + i] = processed_segment
    combined_data = np.concatenate(processed_data)
    wavfile.write("test_groud/result_tuned.wav", sample_rate, combined_data.astype(np.int16))


# 主逻辑
if __name__ == "__main__":
    sample_rate, data = wavfile.read("test_groud/sample/samples/rs4.wav")  # 读取音频数据
    new_sample_rate = 48000
    num_samples = int(len(data) * new_sample_rate / sample_rate)
    resampled_data = resample(data, num_samples)
    tune(resampled_data, new_sample_rate)
