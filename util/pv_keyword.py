import os
import time
from dotenv import load_dotenv
import pvrhino
from pvrecorder import PvRecorder

load_dotenv()

ACCESS_KEY = os.getenv("PV_RHINO_ACCESS_KEY")
CONTEXT_PATH = "/home/denial/denial_payphone/pv_rhino/binary_payphone_response_test_2025_06_07_en_raspberry-pi_v3_0_0.rhn"
DEVICE_INDEX = 1
SILENCE_TIMEOUT_SEC = 8

def wait_for_keyword_response(sensor, on_hook_check=None):
    rhino = pvrhino.create(
        access_key=ACCESS_KEY,
        context_path=CONTEXT_PATH,
    )
    recorder = PvRecorder(
        frame_length=rhino.frame_length,
        device_index=DEVICE_INDEX
    )
    result = None
    try:
        recorder.start()
        start_time = time.monotonic()
        while True:
            if on_hook_check and on_hook_check():
                result = "on_hook"
                break
            if (time.monotonic() - start_time) > SILENCE_TIMEOUT_SEC:
                result = "silence"
                break
            pcm = recorder.read()
            if rhino.process(pcm):
                inf = rhino.get_inference()
                if inf.is_understood:
                    slots = inf.slots
                    if "affirmative" in slots or any(s in slots.values() for s in ("yes", "ok", "sure")):
                        result = "affirmative"
                    elif "negative" in slots or any(s in slots.values() for s in ("no",)):
                        result = "negative"
                    else:
                        result = "not_understood"
                else:
                    result = "not_understood"
                rhino.reset()
                break
    finally:
        recorder.delete()
        rhino.delete()
    return result

