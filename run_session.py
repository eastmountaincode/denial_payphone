# run_session.py

from datetime import datetime

from log import log_event
from audio import play_audio_file, listen_for_amplitude
import general_util
from proximity import is_on_hook

def run_session(sensor, ROOT_DIR, AUDIO_DIR):
    """
    Run a single user session.
    - sensor: the initialized proximity sensor object
    - ROOT_DIR: absolute path to /payphone root
    - AUDIO_DIR: absolute path to prompt .wav files
    """

    #self.session_id = generate_unique_session_id(ROOT_DIR)
    session_id = "session1234" 
    session = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat()
    }
    session["folder"] = general_util.create_session_folder(session_id, ROOT_DIR)
    log_event(session_id, "session_start", session["folder"])
    try:
        finished = play_audio_file("intro_prompt.wav", AUDIO_DIR, lambda: is_on_hook(sensor))
        if not finished:
            log_event(session_id, "session_interrupted_by_on_hook", "User hung up during intro prompt.")
            print("Session interrupted (on-hook during prompt).")
            return

        heard = listen_for_amplitude(threshold=0.1, timeout=6, is_on_hook=lambda: is_on_hook(sensor))
        if heard is None:
            log_event(session_id, "session_interrupted_by_on_hook", "User hung up during listen_for_amplitude.")
            print("Session interrupted (on-hook during listen).")
            return

        if heard:
            log_event(session_id, "amplitude_detected_after_intro")
            finished = play_audio_file("post_intro_user_did_speak.wav", AUDIO_DIR, lambda: is_on_hook(sensor))
            if not finished:
                log_event(session_id, "session_interrupted_by_on_hook", "User hung up during response.")
                print("Session interrupted (on-hook during response).")
                return
        else:
            log_event(session_id, "no_amplitude_detected_after_intro")
            finished = play_audio_file("post_intro_user_did_not_speak.wav", AUDIO_DIR, lambda: is_on_hook(sensor))
            if not finished:
                log_event(session_id, "session_interrupted_by_on_hook", "User hung up during no-speak response.")
                print("Session interrupted (on-hook during response).")
                return

        log_event(session_id, "session_end")
    except Exception as e:
        log_event(session_id, "session_error", str(e))
        print(f"Session {session_id} error: {e}")

