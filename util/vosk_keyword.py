# util/vosk_keyword.py

import json
import time
import queue
import numpy as np
import sounddevice as sd
from vosk import KaldiRecognizer
from config.constants import AUDIO_DEVICE_IN_INDEX, AUDIO_IN_SAMPLE_RATE

# ----------------------------------------------------------------------
# Configuration constants
# ----------------------------------------------------------------------
VOSK_BLOCKSIZE       = 4800        # block size (samples)
SILENCE_TIMEOUT_SEC  = 8           # silence before giving up (sec)
ENERGY_THRESHOLD     = 400         # for is_silence() helper, if needed

# ----------------------------------------------------------------------
# Keyword grammar
# ----------------------------------------------------------------------
AFFIRMATIVE_WORDS = {
    "yes", "yeah", "yep", "affirmative", "sure", "ok", "okay"
}
NEGATIVE_WORDS = {
    "no", "nope", "nah", "negative"
}
KEYWORD_GRAMMAR = json.dumps(sorted(AFFIRMATIVE_WORDS | NEGATIVE_WORDS))

# ----------------------------------------------------------------------
def _is_silence(data: bytes, threshold: int = ENERGY_THRESHOLD) -> bool:
    """RMS-based silence test (optional, for custom logic)."""
    audio = np.frombuffer(data, dtype=np.int16)
    return int(np.abs(audio).mean()) < threshold

def wait_for_keyword_response(sensor, vosk_model, on_hook_check=None) -> str:
    """
    Listen until we hear an affirmative/negative keyword or timeout.
    Returns: "affirmative", "negative", "not_understood", "silence", "on_hook"
    """
    rec        = KaldiRecognizer(vosk_model, AUDIO_IN_SAMPLE_RATE)
    audio_q    = queue.Queue()
    start_time = time.monotonic()

    def _callback(indata, frames, time_info, status):
        if status:
            print("SD-status:", status)
        audio_q.put(bytes(indata))

    with sd.RawInputStream(
        samplerate=AUDIO_IN_SAMPLE_RATE,
        blocksize=VOSK_BLOCKSIZE,
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

                if (time.monotonic() - start_time) > SILENCE_TIMEOUT_SEC:
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

