# External libraries
import uuid
import os
from datetime import datetime
import sys
import time
import sounddevice as sd

# In-house libraries

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from log import log_event
from audio import play_audio_file, listen_for_amplitude
import general_util

ROOT_DIR = "/home/denial/denial_payphone/payphone"
AUDIO_DIR = "/home/denial/denial_payphone/payphone/audio_files/dev"

class Orchestrator:
    def __init__(self):
        #self.session_id = generate_unique_session_id(ROOT_DIR)
        self.session_id = "session1234" # for testing
        self.session = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat()
        }

    def run_session(self):
        # SESSION SETUP
        self.session["folder"] = general_util.create_session_folder(self.session_id, ROOT_DIR)
        log_event(self.session_id, "session_start", self.session["folder"])

        # MAIN EXECUTION
        try:
            play_audio_file("intro_prompt.wav", AUDIO_DIR)
            sd.wait()  # finish playback until checking for amplitude

            heard = listen_for_amplitude(threshold=0.1, timeout=6)

            if heard:
                log_event(self.session_id, "amplitude_detected_after_intro")
                play_audio_file("post_intro_user_did_speak.wav", AUDIO_DIR)
            else:
                log_event(self.session_id, "no_amplitude_detected_after_intro")
                play_audio_file("post_intro_user_did_not_speak.wav", AUDIO_DIR)

            log_event(self.session_id, "session_end")
        except Exception as e:
            log_event(self.session_id, "session_error", str(e))
            print(f"Session {self.session_id} error: {e}")

    def orchestrator_loop(self):
        print("System ready. Waiting for next user.")
        while True:
            self.run_session()
            print("\nReturning to initial state...\n")
            time.sleep(2)

