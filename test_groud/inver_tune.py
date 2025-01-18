import math
import crepe
from scipy.io import wavfile
import numpy as np


# def apply_pitch_shift(spectrogram, phase, semitone_shift, sample_rate, fft_frame_size):
#     """
#     Shifts the pitch of a given spectrogram by a specified number of semitones.
#
#     Args:
#         spectrogram: The amplitude spectrum of the signal.
#         phase: The phase spectrum of the signal.
#         semitone_shift: Number of semitones to shift (positive or negative).
#         sample_rate: Sample rate of the audio signal.
#         fft_frame_size: FFT frame size used for spectrogram analysis.
#
#     Returns:
#         A modified spectrum with pitch shifted.
#     """
#     freq_per_bin = sample_rate / fft_frame_size
#     #print(freq_per_bin)
#     shifted_spectrum = np.zeros(len(spectrogram), dtype=complex)
#
#     for k in range(len(spectrogram)):
#         original_freq = k * freq_per_bin
#         shifted_freq = original_freq * (2 ** (semitone_shift / 12))  # Shift by semitones
#         new_bin = int(np.round(shifted_freq / freq_per_bin))
#
#         if 0 <= new_bin < len(spectrogram):
#             shifted_spectrum[new_bin] += spectrogram[k] * np.exp(1j * phase[k])
#
#     return shifted_spectrum


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
    """
    Applies randomized pitch shifting to an audio file and saves the result.
    """
    # Load audio
    sample_rate, data = wavfile.read(r"C:\Users\David Zhou\Desktop\anyway.wav")
    if data.ndim > 1:  # Handle stereo
        data = data[:, 1]  # Use the right channel for processing

    # Predict pitch using CREPE
    time, frequency, confidence, activation = crepe.predict(
        data, sample_rate, "tiny", viterbi=True, step_size=10
    )

    # # Randomize pitch shift in semitones
    # pitch_shift = np.random.uniform(-5, 5, len(frequency))  # Adjust range as needed
    # Generate pitch shift values using a sine function with a period of 0.5 seconds
    # Generate pitch shift values using a sine function with a specified amplitude and period
    amplitude = 20
    period = 0.5
    pitch_shift = amplitude * np.sin(np.linspace(0, 2 * np.pi * period, len(frequency)))

    fft_frame_size = 4096  # Increase frame size for better quality
    osamp = 4  # Overlap factor
    hop_size = fft_frame_size // osamp  # Frame step size

    # Apply window function
    window = np.hanning(fft_frame_size)
    split_data = [
        data[i: i + fft_frame_size] * window
        for i in range(0, len(data) - fft_frame_size, hop_size)
    ]

    # Perform FFT
    fft_result = [np.fft.fft(segment) for segment in split_data]
    spectrogram = [np.abs(i) for i in fft_result]
    phase = [np.angle(i) for i in fft_result]

    # # Interpolate pitch shift to match spectrogram timing
    # time_original = np.linspace(0, len(data) / sample_rate, len(pitch_shift))
    # time_target = np.linspace(0, len(data) / sample_rate, len(split_data))
    # pitch_shift_interpolated = np.interp(time_target, time_original, pitch_shift)

    # Apply pitch shifting
    shifted_fft = [
        apply_pitch_shift(spectrogram[i], phase[i], pitch_shift[i], sample_rate, fft_frame_size)
        for i in range(len(spectrogram))
    ]

    # Initialize output buffer
    output = np.zeros(len(data))
    for i, frame in enumerate(shifted_fft):
        time_domain = np.fft.ifft(frame).real  # Inverse FFT
        start_idx = i * hop_size
        output[start_idx: start_idx + fft_frame_size] += time_domain * window  # Overlap-add

    # Normalize output
    output = output / np.max(np.abs(output)) * np.max(np.abs(data))

    # Save the modified audio
    wavfile.write("anyway_shifted.wav", sample_rate, output.astype(np.int16))


if __name__ == "__main__":
    tune_and_output()
