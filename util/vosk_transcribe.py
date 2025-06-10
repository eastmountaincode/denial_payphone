# util/vosk_transcribe.py

import queue
import json
import sounddevice as sd
import numpy as np
from vosk import KaldiRecognizer

def vosk_transcribe(vosk_model, device, samplerate, blocksize, max_silence_blocks, prompt_text=None, on_hook_check=None):
    """
    Start real-time transcription with Vosk, stops after silence or on-hook.
    Returns: final transcript (str)
    """
    rec = KaldiRecognizer(vosk_model, samplerate)
    audio_q = queue.Queue()
    heard_speech = False
    silence_count = 0
    result_text = ""

    def is_silence(data, threshold=500):
        audio = np.frombuffer(data, dtype=np.int16)
        return np.abs(audio).mean() < threshold

    def cb(indata, frames, t, status):
        if status:
            print(status)
        audio_q.put(bytes(indata))

    with sd.RawInputStream(
            samplerate=samplerate,
            blocksize=blocksize,
            dtype='int16',
            channels=1,
            device=device,
            callback=cb):
        try:
            while True:
                data = audio_q.get()
                # On-hook check
                if on_hook_check is not None and on_hook_check():
                    print("Session interrupted (on-hook during transcription).")
                    return result_text
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
                        if silence_count >= max_silence_blocks:
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

