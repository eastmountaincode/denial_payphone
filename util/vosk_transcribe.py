# util/vosk_transcribe.py

import queue
import json
import sounddevice as sd
import numpy as np
from vosk import KaldiRecognizer
import time
from config.constants import AUDIO_DEVICE_IN_INDEX, AUDIO_IN_SAMPLE_RATE

VOSK_BLOCKSIZE      = 4800
MAX_SILENCE_BLOCKS = 30      # 3 seconds
ENERGY_THRESHOLD   = 400

def vosk_transcribe(vosk_model, max_initial_silence=6, on_hook_check=None):
    """
    Start real-time transcription with Vosk, stops after silence or on-hook.
    Returns: final transcript (str)
    """
    rec = KaldiRecognizer(vosk_model, AUDIO_IN_SAMPLE_RATE)
    audio_q = queue.Queue()
    heard_speech = False
    silence_count = 0
    result_text = ""
    start_time = time.time()

    def is_silence(data, threshold=ENERGY_THRESHOLD):
        audio = np.frombuffer(data, dtype=np.int16)
        return np.abs(audio).mean() < threshold

    def cb(indata, frames, t, status):
        if status:
            print(status)
        audio_q.put(bytes(indata))

    with sd.RawInputStream(
            samplerate=AUDIO_IN_SAMPLE_RATE,
            blocksize=VOSK_BLOCKSIZE,
            dtype='int16',
            channels=1,
            device=AUDIO_DEVICE_IN_INDEX,
            callback=cb):
        try:
            while True:
                data = audio_q.get()
                now = time.time()

                # On-hook check
                if on_hook_check is not None and on_hook_check():
                    print("Session interrupted (on-hook during transcription).")
                    return result_text

                # Move on if initial silence is too long
                if not heard_speech and (now - start_time > max_initial_silence):
                    print(f"No speech detected after {max_initial_silence} seconds, exiting transcription.")
                    return ""
 
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    txt = result.get("text", "")
                    if txt.strip():
                        print(">>", txt)
                        result_text += txt + " "
                        heard_speech = True
                        silence_count = 0
                elif heard_speech:
                    if is_silence(data):
                        silence_count += 1
                        if silence_count >= MAX_SILENCE_BLOCKS:
                            print("(Detected silence after speech, stopping…)\n")
                            break
                    else:
                        silence_count = 0
        except KeyboardInterrupt:
            print("Transcription stopped by user.")
        # Get final result
        final_txt = json.loads(rec.FinalResult()).get("text", "")
        if final_txt:
            print("Final:", final_txt)
            result_text += final_txt
        return result_text.strip()


def transcription_worker(vosk_model, sr, audio_queue, transcript_parts, transcript_lock, stop_transcription, speech_detected_event=None, last_word_time=None):
    """Background thread worker for processing audio transcription"""
    rec = KaldiRecognizer(vosk_model, sr)
    
    def float32_to_int16(audio_data):
        """Convert float32 audio data to int16 for Vosk"""
        if audio_data.ndim > 1:
            audio_data = audio_data.flatten()
        audio_clipped = np.clip(audio_data, -1.0, 1.0)
        return (audio_clipped * 32767).astype(np.int16)
    
    while not stop_transcription.is_set():
        try:
            # Get audio chunk from queue (timeout so we can check stop_transcription)
            audio_chunk = audio_queue.get(timeout=0.1)
            
            # Process with Vosk
            int16_data = float32_to_int16(audio_chunk)
            if rec.AcceptWaveform(int16_data.tobytes()):
                try:
                    result = json.loads(rec.Result())
                    text = result.get("text", "")
                    if text.strip():
                        with transcript_lock:
                            transcript_parts.append(text.strip())
                        print(f"[LIVE TRANSCRIPT]: {text}")
                        # Signal that we've detected speech via transcription
                        if speech_detected_event:
                            speech_detected_event.set()
                        # Update last word timestamp
                        if last_word_time is not None:
                            last_word_time['time'] = time.time()
                except json.JSONDecodeError:
                    pass
                    
            audio_queue.task_done()
            
        except queue.Empty:
            continue  # Check stop_transcription flag
        except Exception as e:
            print(f"[TRANSCRIPTION WARNING]: {e}")
    
    # Process any remaining audio and get final result
    try:
        final_result = json.loads(rec.FinalResult())
        final_text = final_result.get("text", "")
        if final_text.strip():
            with transcript_lock:
                transcript_parts.append(final_text.strip())
            print(f"[FINAL TRANSCRIPT]: {final_text}")
            # Signal that we've detected speech via transcription
            if speech_detected_event:
                speech_detected_event.set()
            # Update last word timestamp
            if last_word_time is not None:
                last_word_time['time'] = time.time() 
    except json.JSONDecodeError:
        print("[WARNING]: Could not parse final transcription result")

