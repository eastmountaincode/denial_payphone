import os
import sys
import time
from datetime import datetime
import sounddevice as sd
from vosk import Model
import fasttext

# In-house libraries
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from proximity import (
    init_proximity_sensor,
    wait_for_off_hook,
    wait_for_on_hook_with_dialtone,
)
from session_fsm import run_session
from audio import play_audio_file

from config.constants import ROOT_DIR, AUDIO_DIR, VOSK_MODEL_PATH, FASTTEXT_MODEL_PATH

class Orchestrator:
    def __init__(self):
        self.sensor = init_proximity_sensor()
        
        self.vosk_model = Model(VOSK_MODEL_PATH)

        print("[ORCHESTRATOR] Loading fastText model...")
        self.fasttext_model = fasttext.load_model(FASTTEXT_MODEL_PATH)
        print("[ORCHESTRATOR] fastText model loaded successfully.")

    def orchestrator_loop(self):
        print("[ORCHESTRATOR] System ready. Waiting for next user.")
        while True:
            print("[ORCHESTRATOR] Waiting for phone to go off-hook...")
            wait_for_off_hook(self.sensor)

            print("[ORCHESTRATOR] Off-hook detected, starting session.")
            play_audio_file("enter_sfx.wav", AUDIO_DIR)

            run_session(self.sensor,
                        ROOT_DIR,
                        AUDIO_DIR, 
                        self.vosk_model,
                        self.fasttext_model)

            print("[ORCHESTRATOR] Session ended. Waiting for phone to go back on-hook...")
            wait_for_on_hook_with_dialtone(self.sensor, "dial_tone_loop_v1.wav", AUDIO_DIR)

            print("[ORCHESTRATOR] On-hook detected. Returning to initial state...\n")
            play_audio_file("exit_sfx.wav", AUDIO_DIR)

            time.sleep(1)

if __name__ == "__main__":
    try:
        orchestrator = Orchestrator()
        orchestrator.orchestrator_loop()
    except KeyboardInterrupt:
        print("\n[ORCHESTRATOR] Shutting down (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"[ORCHESTRATOR] Error: {e}")

