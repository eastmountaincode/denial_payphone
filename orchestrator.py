import time
import uuid
import os
from datetime import datetime
from log import log_event 

SESSION_ROOT = "/home/denial/denial_payphone/payphone"

def wait_for_rfid():
    print("Waiting for RFID swipe...")
    # TODO: Replace with real RFID detection code
    time.sleep(1)
    return "rfid_1234"

def play_audio(prompt):
    print(f"[AUDIO] {prompt}")
    # TODO: Replace with real audio playback
    time.sleep(1)

def listen_for_keyword():
    print("Listening for keyword (yes/no/ok/sure)...")
    # TODO: Replace with real keyword detection
    time.sleep(1)
    return "yes"

def transcribe_and_save(session):
    print(f"Transcribing and saving audio for run {session['run_id']}")
    # TODO: Replace with real transcription
    time.sleep(1)
    return "user said something"

def create_session_folder(run_id):
    folder = os.path.join(SESSION_ROOT, run_id)
    os.makedirs(folder, exist_ok=True)
    print(f"Created session folder: {folder}")
    return folder

'''
run_session is within the domain of Orchestrator.
Orchestrator is responsible for logging.

session - dict: acts as state
'''
def run_session():
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    session = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat()
    }
    session["folder"] = create_session_folder(run_id)
    log_event(session_id, "session_start", session["folder"])

    try:
        rfid = wait_for_rfid()
        log_event(session_id, "rfid_detected", rfid)
        session["rfid"] = rfid

        play_audio("welcome_prompt")
        response = listen_for_keyword()
        log_event(run_id, "keyword_detected", response)

        if response.lower() not in ["yes", "ok", "sure"]:
            log_event(run_id, "user_declined")
            play_audio("goodbye_prompt")
            return

        play_audio("start_recording_prompt")
        result = transcribe_and_save(session)
        log_event(session_id, "transcription", result)

        play_audio("thank_you_prompt")
        log_event(run_id, "session_end")
    except Exception as e:
        log_event(run_id, "session_error", str(e))
        print(f"Session {run_id} error: {e}")

def orchestrator_loop():
    print("System ready. Waiting for next user.")
    while True:
        run_session()
        print("\nReturning to initial state...\n")
        time.sleep(2)

if __name__ == "__main__":
    orchestrator_loop()

