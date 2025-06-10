# External libraries

import uuid
import os
from datetime import datetime
import sys
import time
import threading
import sounddevice as sd
import multiprocessing

# In-house libraries

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from log import log_event
from proximity import init_proximity_sensor, wait_for_off_hook, wait_for_on_hook
import general_util

ROOT_DIR = "/home/denial/denial_payphone/payphone"

def session_process(session_id):
    from run_session import run_session  
    run_session(session_id)

class Orchestrator:
    def __init__(self):
        self.sensor = init_proximity_sensor() # creates the VCNL4200 sensor object

    def session_process(self, session_id):
        from run_session import run_session  
        run_session(session_id)

    def orchestrator_loop(self):
        print("System ready. Waiting for next user.")
        ctx = multiprocessing.get_context("spawn")
        while True:
            print("Waiting for phone to go off-hook...")
            wait_for_off_hook(self.sensor)
            print("Off-hook detected, starting session.")

            #session_id = general_util.generate_unique_session_id(self.ROOT_DIR)
            session_id = "session1234"

            
            session_proc = ctx.Process(target=session_process, args=(session_id,))
            session_proc.start()

            wait_for_on_hook(self.sensor)
            print("On-hook detected. Terminating session if still running.")

            if session_proc.is_alive():
                session_proc.terminate()  # Safely kills the process immediately
                session_proc.join(timeout=1)

            print("Returned to initial state.\n")
            time.sleep(2)

if __name__ == "__main__":
    try:
        orchestrator = Orchestrator()
        orchestrator.orchestrator_loop()
    except Exception as e:
        print(f"Error: {e}")

