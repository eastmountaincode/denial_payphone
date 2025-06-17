# util/vosk_keyword.py

import json
import time
import queue
import numpy as np
import sounddevice as sd
from vosk import KaldiRecognizer
from config.constants import AUDIO_DEVICE_IN_INDEX, AUDIO_IN_SAMPLE_RATE, KEYWORD_SILENCE_TIMEOUT_SEC

# ----------------------------------------------------------------------
# Keyword grammar
# ----------------------------------------------------------------------
AFFIRMATIVE_WORDS = {
    "yes", "yeah", "yep", "affirmative", "sure", "ok", "okay"
}
NEGATIVE_WORDS = {
    "no", "nope", "nah", "negative"
}
# ----------------------------------------------------------------------


def wait_for_keyword_response(vosk_model, on_hook_check=None) -> str:
    """
    Listen until we hear an affirmative/negative keyword or timeout.
    Returns: "affirmative", "negative", "not_understood", "silence", "on_hook"
    """
    rec        = KaldiRecognizer(vosk_model, AUDIO_IN_SAMPLE_RATE)
    audio_q    = queue.Queue()
    start_time = time.monotonic()
    blocksize  = 4800

    # Callback runs in separate thread, queues incoming audio data for processing
    def _callback(indata, frames, time_info, status):
        if status:
            print("SD-status:", status)
        audio_q.put(bytes(indata))

    with sd.RawInputStream(
        samplerate=AUDIO_IN_SAMPLE_RATE,
        blocksize=blocksize,
        dtype="int16",
        channels=1,
        device=AUDIO_DEVICE_IN_INDEX,
        callback=_callback,
    ):
        try:
            while True:
                data = audio_q.get()

                if on_hook_check and on_hook_check():
                    return "on_hook"

                if (time.monotonic() - start_time) > KEYWORD_SILENCE_TIMEOUT_SEC:
                    return "silence"
 
                if rec.AcceptWaveform(data):           # ← True ⇒ we have a full utterance
                    result = json.loads(rec.Result())
                    recognised = result.get("text", "").lower().strip()
                    if not recognised:
                        continue

                    tokens = set(recognised.split())

                    if tokens & AFFIRMATIVE_WORDS:
                        return "affirmative"
                    if tokens & NEGATIVE_WORDS:
                        return "negative"
                    return "not_understood"
               
        finally:
            pass
