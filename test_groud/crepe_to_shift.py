import crepe
from scipy.io import wavfile
import numpy as np
from standard_pitch import predict_to_standard


def reconstruct_fft(spectrogram, phase):
    return [magnitude * np.exp(1j * angle) for magnitude, angle in zip(spectrogram, phase)]


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
def tune_and_output():
    sample_rate, data = wavfile.read("sample/samples/rs4.wav")  # sample rate = 44100
    time, frequency, confidence, activation = crepe.predict(
        data, sample_rate, "tiny", viterbi=True, step_size=10
    )
    pitch_shift = frequency - np.array([predict_to_standard(i) for i in frequency])
    fft_frame_size = 2048  # ]increase framesize
    osamp = 4  # 重叠的因子  maybe？
    hop_size = fft_frame_size // osamp  # frame step

    split_data = [
        data[i : i + fft_frame_size] * np.hanning(fft_frame_size)
        for i in range(0, len(data) - fft_frame_size, hop_size)
    ]
    fft_result = [np.fft.fft(segment) for segment in split_data]
    spectrogram = [np.abs(i) for i in fft_result]
    phase = [np.angle(i) for i in fft_result]
    time_original = np.linspace(0, len(data) / sample_rate, len(pitch_shift))
    time_target = np.linspace(0, len(data) / sample_rate, len(split_data))
    pitch_shift_interpolated = np.interp(time_target, time_original, pitch_shift)

    # where we shift pitch
    shifted_fft = [
        apply_pitch_shift(spectrogram[i], phase[i], pitch_shift_interpolated[i], sample_rate, fft_frame_size)
        for i in range(len(spectrogram))
    ]
    output = np.zeros(len(data))  # initialize output
    for i, frame in enumerate(shifted_fft):
        time_domain = np.fft.ifft(frame).real
        start_idx = i * hop_size
        output[start_idx : start_idx + fft_frame_size] += time_domain
    wavfile.write("../result_pitch.wav", sample_rate, output.astype(np.int16))



if __name__ == "__main__":
    tune_and_output()