# External libraries

import uuid
import os
from datetime import datetime
import sys
import time

# In-house libraries

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from log import log_event 
from audio import play_audio_file
import general_util

ROOT_DIR = "/home/denial/denial_payphone/payphone"
AUDIO_DIR = "/home/denial/denial_payphone/payphone/audio_files/dev"

'''
run_session is within the domain of Orchestrator.
Orchestrator is responsible for logging.

session - dict: acts as state
'''
def run_session():
    #session_id = f"session_{uuid.uuid4().hex[:8]}"
    session_id = "session_1234"
    session = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat()
    }
    session["folder"] = general_util.create_session_folder(session_id, ROOT_DIR)
    log_event(session_id, "session_start", session["folder"])

    try:
        play_audio_file("hello_payphone.wav", AUDIO_DIR)

        log_event(session_id, "session_end")
    except Exception as e:
        log_event(session_id, "session_error", str(e))
        print(f"Session {session_id} error: {e}")

def orchestrator_loop():
    print("System ready. Waiting for next user.")
    while True:
        run_session()
        print("\nReturning to initial state...\n")
        time.sleep(2)

if __name__ == "__main__":
    try:
        orchestrator_loop()
    except KeyboardInterrupt:
        print("\nShutting down gracefully (Ctrl+C detected).")
        log_event("SYSTEM", "shutdown", "KeyboardInterrupt (Ctrl+C)")
        sys.exit(0)

