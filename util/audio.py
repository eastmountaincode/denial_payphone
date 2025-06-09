import os
import sounddevice as sd
import soundfile as sf
import numpy 
import time

def play_audio_file(filename, AUDIO_DIR):
    """
    Plays a .wav file using sounddevice.OutputStream. Returns the stream.
    Orchestrator can call .close() to stop early or poll .active to know if playing.
    """
    if not os.path.isabs(filename):
        filepath = os.path.join(AUDIO_DIR, filename)
    else:
        filepath = filename

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Audio file not found: {filepath}")

    data, samplerate = sf.read(filepath, dtype='float32')
    channels = data.shape[1] if data.ndim > 1 else 1

    stream = sd.OutputStream(samplerate=samplerate, channels=channels)
    stream.start()
    stream.write(data)
    return stream

def listen_for_amplitude(threshold=0.02, timeout=6, samplerate=44100, blocksize=1024, device=None):
    """
    Listen for any sound above a threshold on the default mic.
    Returns True if detected, False if timed out.

    Usage:

        if listenForAmplitude():
            # Detected sound
        else:
            # Timed out, no sound detected
    """
    start_time = time.time()

    stream_args = {
        'samplerate': samplerate,
        'channels': 1,
        'dtype': 'float32',
        'blocksize': blocksize,
        'device': device
    }

    with sd.InputStream(**stream_args) as stream:
        while True:
            data, _ = stream.read(blocksize)
            amplitude = np.abs(data).max()
            if amplitude > threshold:
                return True
            if time.time() - start_time > timeout:
                return False

