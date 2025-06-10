import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time

AUDIO_DEVICE_OUT = 1 
AUDIO_DEVICE_IN = 1   

def play_audio_file(filename, AUDIO_DIR, is_on_hook: callable, chunk_size=2048):
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

    with sd.OutputStream(samplerate=samplerate, channels=channels, device=AUDIO_DEVICE_OUT) as stream:
        start = 0
        while start < len(data):
            end = min(start + chunk_size, len(data))
            stream.write(data[start:end])
            start = end
            if is_on_hook():
                stream.abort()
                return False
    return True

def listen_for_amplitude(threshold=0.02, timeout=6, samplerate=44100, blocksize=1024, is_on_hook: callable):
    """
    Listen for any sound above a threshold on the default mic,
    checking is_on_hook() between blocks.
    Returns True if detected, False if timed out, or None if interrupted.
    """
    start_time = time.time()

    stream_args = {
        'samplerate': samplerate,
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

