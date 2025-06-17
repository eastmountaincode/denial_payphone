import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import threading
import queue
from vosk_transcribe import transcription_worker
from pydub import AudioSegment

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
                         threshold=0.015,
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
    block_dur = 0.18  # 180 ms blocks
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
    speech_detected_by_vosk = threading.Event()  # Signal from transcription worker
    last_word_time = {'time': None}  # Shared timestamp for last transcribed word
    
    # Start transcription worker thread
    transcription_thread = threading.Thread(
        target=transcription_worker, 
        args=(vosk_model, sr, audio_queue, transcript_parts, transcript_lock, stop_transcription, speech_detected_by_vosk, last_word_time),
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


def save_audio_compressed(audio_np, sr, output_path, compression_level=5):
    """
    Save audio with 16-bit FLAC compression and measure timing.
    
    Args:
        audio_np: numpy audio array (float32)
        sr: sample rate
        output_path: path for output file (should end with .flac)
        compression_level: FLAC compression level 0-8 (default 5 for good speed/size balance)
    
    Returns:
        dict with timing and size info
    """
    start_time = time.time()
    
    # Step 1: Convert to int16 for size reduction
    audio_int16 = (np.clip(audio_np, -1.0, 1.0) * 32767).astype(np.int16)
    int16_time = time.time()
    
    # Step 2: Create temporary uncompressed WAV file for size comparison
    temp_wav_path = output_path.replace('.flac', '_temp.wav')
    sf.write(temp_wav_path, audio_int16, sr, subtype='PCM_16')
    wav_time = time.time()
    
    # Step 3: Save directly as FLAC (much faster than MP3)
    sf.write(output_path, audio_int16, sr, subtype='PCM_16', format='FLAC', compression=compression_level)
    flac_time = time.time()
    
    # Step 4: Clean up temp file and get sizes
    temp_size = os.path.getsize(temp_wav_path)
    os.remove(temp_wav_path)
    final_size = os.path.getsize(output_path)
    
    end_time = time.time()
    
    # Return timing and compression info
    return {
        'total_time': end_time - start_time,
        'int16_conversion_time': int16_time - start_time,
        'wav_write_time': wav_time - int16_time,
        'flac_conversion_time': flac_time - wav_time,
        'temp_size_bytes': temp_size,
        'final_size_bytes': final_size,
        'compression_ratio': temp_size / final_size,
        'size_reduction_percent': (1 - final_size / temp_size) * 100
    }


