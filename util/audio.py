import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time

AUDIO_DEVICE_OUT = 1 
AUDIO_DEVICE_IN = 1   
SAMPLE_RATE = 48000


def play_audio_file(filename, AUDIO_DIR, is_on_hook: callable = None, chunk_size=2048):
    """
    Play a .wav file in small chunks, checking is_on_hook() between each.
    Returns True if playback completed, False if interrupted (on-hook).
    """
    if not os.path.isabs(filename):
        filepath = os.path.join(AUDIO_DIR, filename)
    else:
        filepath = filename
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Audio file not found: {filepath}")

    data, samplerate = sf.read(filepath, dtype='float32')
    channels = data.shape[1] if data.ndim > 1 else 1

    desired_samplerate = SAMPLE_RATE
    if samplerate != desired_samplerate:
        data, samplerate = resample_audio(data, samplerate, desired_samplerate)

    with sd.OutputStream(samplerate=samplerate, channels=channels, device=AUDIO_DEVICE_OUT) as stream:
        start = 0
        while start < len(data):
            end = min(start + chunk_size, len(data))
            stream.write(data[start:end])
            start = end
            if is_on_hook and is_on_hook():
                stream.abort()
                return False
    return True

def listen_for_amplitude(threshold, timeout, is_on_hook: callable, blocksize=1024):
    """
    Listen for any sound above a threshold on the default mic,
    checking is_on_hook() between blocks.
    Returns True if detected, False if timed out, or None if interrupted.
    """
    start_time = time.time()

    stream_args = {
        'samplerate': SAMPLE_RATE,
        'channels': 1,
        'dtype': 'float32',
        'blocksize': blocksize,
        'device': AUDIO_DEVICE_IN
    }

    with sd.InputStream(**stream_args) as stream:
        while True:
            data, _ = stream.read(blocksize)
            amplitude = np.abs(data).max()
            if amplitude > threshold:
                return True
            if time.time() - start_time > timeout:
                return False
            if is_on_hook():
                return None

def resample_audio(data, orig_sr, target_sr):
    """
    Resample numpy audio array from orig_sr to target_sr. Returns float32 array.
    Handles mono or multi-channel.
    """
    if orig_sr == target_sr:
        return data, orig_sr
    ratio = target_sr / orig_sr
    num_samples = int(len(data) * ratio)
    if data.ndim == 1:
        resampled = np.interp(
            np.linspace(0, len(data), num_samples, endpoint=False),
            np.arange(len(data)),
            data
        )
    else:
        # Multi-channel: resample each channel separately
        resampled = np.vstack([
            np.interp(
                np.linspace(0, len(data), num_samples, endpoint=False),
                np.arange(len(data)),
                data[:, ch]
            ) for ch in range(data.shape[1])
        ]).T
    return resampled.astype('float32'), target_sr


