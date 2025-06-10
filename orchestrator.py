import os
import sys
import time
from datetime import datetime
import sounddevice as sd

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

ROOT_DIR = "/home/denial/denial_payphone/payphone"
AUDIO_DIR = "/home/denial/denial_payphone/payphone/audio_files/dev"

class Orchestrator:
    def __init__(self):
        self.sensor = init_proximity_sensor()

    def orchestrator_loop(self):
        print("System ready. Waiting for next user.")
        while True:
            print("Waiting for phone to go off-hook...")
            wait_for_off_hook(self.sensor)
            print("Off-hook detected, starting session.")

            run_session(self.sensor, ROOT_DIR, AUDIO_DIR)

            print("Session ended. Waiting for phone to go back on-hook...")
            wait_for_on_hook(self.sensor)
            print("On-hook detected. Returning to initial state...\n")
            time.sleep(2)

if __name__ == "__main__":
    try:
        orchestrator = Orchestrator()
        orchestrator.orchestrator_loop()
    except Exception as e:
        print(f"Error: {e}")

