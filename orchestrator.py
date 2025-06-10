import os
import sys
import time
from datetime import datetime
import sounddevice as sd
from vosk import Model

# In-house libraries
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from proximity import (
    init_proximity_sensor,
    wait_for_off_hook,
    wait_for_on_hook,
)
from run_session import run_session
from audio import play_audio_file

ROOT_DIR = "/home/denial/denial_payphone/payphone"
AUDIO_DIR = "/home/denial/denial_payphone/payphone/audio_files/dev"

VOSK_MODEL_PATH  = "/home/denial/denial_payphone/vosk/models/vosk-model-small-en-us-0.15"


class Orchestrator:
    def __init__(self):
        self.sensor = init_proximity_sensor()
        self.vosk_model = Model(VOSK_MODEL_PATH)

    def orchestrator_loop(self):
        print("System ready. Waiting for next user.")
        while True:
            print("Waiting for phone to go off-hook...")
            wait_for_off_hook(self.sensor)

            print("Off-hook detected, starting session.")
            play_audio_file("enter_sfx.wav", AUDIO_DIR)

            run_session(self.sensor,
                        ROOT_DIR,
                        AUDIO_DIR, 
                        self.vosk_model)

            print("Session ended. Waiting for phone to go back on-hook...")
            wait_for_on_hook(self.sensor)

            print("On-hook detected. Returning to initial state...\n")
            play_audio_file("exit_sfx.wav", AUDIO_DIR)

            time.sleep(1)

if __name__ == "__main__":
    try:
        orchestrator = Orchestrator()
        orchestrator.orchestrator_loop()
    except KeyboardInterrupt:
        print("\nShutting down (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}")

