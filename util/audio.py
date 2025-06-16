import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
import json
from vosk import KaldiRecognizer

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
                         trailing_silence=6.0,
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
    block_dur = 0.3  # 100 ms blocks
    block_size = int(sr * block_dur)
    max_init_blocks = int(max_initial_silence / block_dur)
    trailing_blocks = int(trailing_silence / block_dur)
    
    # Recording state
    speech_detected = False
    trailing_cnt = 0
    frames = []
    
    # Transcription setup
    rec = KaldiRecognizer(vosk_model, sr)
    transcript_parts = []
    
    # Audio buffer for transcription (convert float32 to int16)
    def float32_to_int16(audio_data):
        """Convert float32 audio data to int16 for Vosk"""
        # Ensure we have the right shape and range
        if audio_data.ndim > 1:
            audio_data = audio_data.flatten()
        # Clip to [-1.0, 1.0] range and convert to int16
        audio_clipped = np.clip(audio_data, -1.0, 1.0)
        return (audio_clipped * 32767).astype(np.int16)

    with sd.InputStream(channels=1,
                        samplerate=sr,
                        blocksize=block_size,
                        device=device_index,
                        dtype='float32') as stream:
        while True:
            if on_hook_check and on_hook_check():
                return "on_hook", None, ""

            data, _ = stream.read(block_size)
            rms = np.sqrt(np.mean(data ** 2))
            
            # Always store audio data (start recording immediately)
            frames.append(data.copy())
            
            # Always process audio for transcription (start transcribing immediately)
            int16_data = float32_to_int16(data)
            if rec.AcceptWaveform(int16_data.tobytes()):
                # Get partial result
                try:
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text.strip():
                        transcript_parts.append(text.strip())
                        print(f"[LIVE TRANSCRIPT]: {text}")
                except json.JSONDecodeError:
                    # Skip malformed JSON responses
                    pass
            
            # Check if we've detected speech for the first time
            if not speech_detected:
                if rms >= threshold:
                    speech_detected = True
                    print("[RECORDING]: Speech detected...")
                else:
                    max_init_blocks -= 1
                    if max_init_blocks <= 0:
                        return "silence", None, ""
                        
            # Check for silence to end recording (only after speech detected)
            if speech_detected:
                trailing_cnt = trailing_cnt + 1 if rms < threshold else 0
                if trailing_cnt >= trailing_blocks:
                    print("[RECORDING]: Silence detected, ending recording...")
                    break

    # Get final transcription result
    try:
        final_result = json.loads(rec.FinalResult())
        final_text = final_result.get("text", "")
        if final_text.strip():
            transcript_parts.append(final_text.strip())
            print(f"[FINAL TRANSCRIPT]: {final_text}")
    except json.JSONDecodeError:
        print("[WARNING]: Could not parse final transcription result")
    
    # Combine all audio frames
    if frames:
        audio_np = np.concatenate(frames, axis=0)
    else:
        audio_np = np.array([])
    
    # Combine all transcript parts
    full_transcript = " ".join(transcript_parts).strip()
    
    print(f"[RECORDING COMPLETE]: Audio length: {len(audio_np)} samples, Transcript: '{full_transcript[:50]}{'...' if len(full_transcript) > 50 else ''}'")
    
    return "audio", audio_np, full_transcript


