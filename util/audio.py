import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import threading
import queue
from vosk_transcribe import transcription_worker

AUDIO_DEVICE_OUT = 1 
AUDIO_DEVICE_IN = 1   
SAMPLE_RATE = 48000

def play_audio_file(filename, AUDIO_DIR, is_on_hook: callable = None, chunk_size=2048):
    """
    Play a .wav file in small chunks, checking is_on_hook() between each.
    Returns True if playback completed, False if interrupted (on-hook).
    """
    #time.sleep(0.75)
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

def record_and_transcribe(vosk_model,
                         threshold=0.013,
                         max_initial_silence=10.0,
                         trailing_silence=4.5,
                         sr=48000,
                         device_index=1,
                         on_hook_check=None):
    """
    Record audio while simultaneously transcribing with Vosk.
    Returns tuple (status, audio_np_array, transcript)
        status:
            "audio"     – user spoke, audio and transcript returned
            "silence"   – 10 s of total silence, no audio
            "on_hook"   – handset replaced during record
        audio_np_array: recorded audio as numpy array (or None)
        transcript: full transcribed text (or empty string)
    """
    # Recording parameters
    block_dur = 0.15  # 150 ms blocks
    block_size = int(sr * block_dur)
    max_init_blocks = int(max_initial_silence / block_dur)
    trailing_blocks = int(trailing_silence / block_dur)
    
    # Recording state
    speech_detected = False
    trailing_cnt = 0
    frames = []
    
    # Transcription setup with threading
    audio_queue = queue.Queue()
    transcript_parts = []
    transcript_lock = threading.Lock()
    stop_transcription = threading.Event()
    
    # Start transcription worker thread
    transcription_thread = threading.Thread(
        target=transcription_worker, 
        args=(vosk_model, sr, audio_queue, transcript_parts, transcript_lock, stop_transcription),
        daemon=True
    )
    transcription_thread.start()

    with sd.InputStream(channels=1,
                        samplerate=sr,
                        blocksize=block_size,
                        device=device_index,
                        dtype='float32') as stream:
        while True:
            if on_hook_check and on_hook_check():
                return "on_hook", None, ""

            # Read audio data (this must be fast and not block)
            data, _ = stream.read(block_size)
            
            # Always store audio data immediately (highest priority)
            frames.append(data.copy())
            
            # Calculate RMS for speech detection
            rms = np.sqrt(np.mean(data ** 2))
            
            # Check if we've detected speech for the first time
            if not speech_detected:
                if rms >= threshold:
                    speech_detected = True
                    print("[RECORDING]: Speech detected...")
                else:
                    max_init_blocks -= 1
                    if max_init_blocks <= 0:
                        return "silence", None, ""
            
            # Send audio to transcription thread (non-blocking)
            try:
                audio_queue.put_nowait(data.copy())
            except queue.Full:
                # If queue is full, skip this chunk - audio recording continues
                print("[TRANSCRIPTION]: Queue full, skipping chunk")
                        
            # Check for silence to end recording (only after speech detected)
            if speech_detected:
                trailing_cnt = trailing_cnt + 1 if rms < threshold else 0
                if trailing_cnt >= trailing_blocks:
                    print("[RECORDING]: Silence detected, ending recording...")
                    break

    # Stop transcription thread and wait for it to finish
    stop_transcription.set()
    
    # Wait for transcription queue to be processed
    audio_queue.join()
    
    # Wait for transcription thread to complete
    transcription_thread.join(timeout=2.0)
    
    # Combine all audio frames
    if frames:
        audio_np = np.concatenate(frames, axis=0)
    else:
        audio_np = np.array([])
    
    # Combine all transcript parts (thread-safe)
    with transcript_lock:
        full_transcript = " ".join(transcript_parts).strip()
    
    print(f"[RECORDING COMPLETE]: Audio length: {len(audio_np)} samples, Transcript: '{full_transcript[:50]}{'...' if len(full_transcript) > 50 else ''}'")
    
    return "audio", audio_np, full_transcript


