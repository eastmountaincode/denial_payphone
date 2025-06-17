import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import threading
import queue
from vosk_transcribe import transcription_worker
from config.constants import (
    AUDIO_DEVICE_OUT_INDEX,
    AUDIO_DEVICE_IN_INDEX,
    AUDIO_IN_SAMPLE_RATE,
    AUDIO_OUT_SAMPLE_RATE,
    AUDIO_SAVE_SAMPLE_RATE,
)
  


def play_audio_file(filename, AUDIO_DIR, is_on_hook: callable = None, chunk_size=2048):
    """
    Play a .wav file in small chunks, checking is_on_hook() between each.
    Returns True if playback completed, False if interrupted (on-hook).
    play_and_log() in general_util.py uses this function.
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

    with sd.OutputStream(samplerate=AUDIO_OUT_SAMPLE_RATE, channels=channels, device=AUDIO_DEVICE_OUT_INDEX) as stream:
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
        'samplerate': AUDIO_IN_SAMPLE_RATE,
        'channels': 1,
        'dtype': 'float32',
        'blocksize': blocksize,
        'device': AUDIO_DEVICE_IN_INDEX
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

def record_and_transcribe(vosk_model,
                         threshold=0.02,
                         max_initial_silence=10.0,
                         trailing_silence=3.0,
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
    block_dur = 0.18  # 180 ms blocks
    block_size = int(AUDIO_IN_SAMPLE_RATE * block_dur)
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
    speech_detected_by_vosk = threading.Event()  # Signal from transcription worker
    last_word_time = {'time': None}  # Shared timestamp for last transcribed word
    
    # Start transcription worker thread
    transcription_thread = threading.Thread(
        target=transcription_worker, 
        args=(vosk_model, AUDIO_IN_SAMPLE_RATE, audio_queue, transcript_parts, transcript_lock, stop_transcription, speech_detected_by_vosk, last_word_time),
        daemon=True
    )
    transcription_thread.start()

    with sd.InputStream(channels=1,
                        samplerate=AUDIO_IN_SAMPLE_RATE,
                        blocksize=block_size,
                        device=AUDIO_DEVICE_IN_INDEX,
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
                # Check both RMS threshold AND if Vosk has detected speech
                if rms >= threshold or speech_detected_by_vosk.is_set():
                    speech_detected = True
                    detection_method = "amplitude" if rms >= threshold else "transcription"
                    print(f"[RECORDING]: Speech detected via {detection_method}...")
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
                # Check RMS silence
                rms_silence = rms < threshold
                
                # Check Vosk silence (no words for trailing_silence duration)
                current_time = time.time()
                vosk_silence = (last_word_time['time'] is None or 
                               (current_time - last_word_time['time']) > trailing_silence)
                
                # Only count as silence if BOTH RMS and Vosk indicate silence
                if rms_silence and vosk_silence:
                    trailing_cnt += 1
                    if trailing_cnt >= trailing_blocks:
                        print("[RECORDING]: Dual silence detected (amplitude + transcription), ending recording...")
                        break
                else:
                    trailing_cnt = 0  # Reset if either RMS or Vosk indicates activity

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


def save_audio_compressed(audio_np, output_path):
    """
    Save audio with 16-bit FLAC compression.
    
    Args:
        audio_np: numpy audio array (float32)
        sr: sample rate
        output_path: path for output file (should end with .flac)
    """
    # Convert to int16 and save as FLAC
    audio_int16 = (np.clip(audio_np, -1.0, 1.0) * 32767).astype(np.int16)
    sf.write(output_path, audio_int16, AUDIO_SAVE_SAMPLE_RATE, subtype='PCM_16', format='FLAC')


