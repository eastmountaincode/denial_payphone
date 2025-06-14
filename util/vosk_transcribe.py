# util/vosk_transcribe.py

import queue
import json
import sounddevice as sd
import numpy as np
from vosk import KaldiRecognizer
import time

VOSK_DEVICE         = 1          
VOSK_SR             = 48000
VOSK_BLOCKSIZE      = 4800
MAX_SILENCE_BLOCKS = 30      # 3 seconds
ENERGY_THRESHOLD   = 400


def vosk_transcribe(vosk_model, max_initial_silence=6, on_hook_check=None):
    """
    Start real-time transcription with Vosk, stops after silence or on-hook.
    Returns: final transcript (str)
    """
    rec = KaldiRecognizer(vosk_model, VOSK_SR)
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
            samplerate=VOSK_SR,
            blocksize=VOSK_BLOCKSIZE,
            dtype='int16',
            channels=1,
            device=VOSK_DEVICE,
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

