def run_session(session_id):

    import os
    from datetime import datetime
    import sys
    import sounddevice as sd
    import soundfile as sf
    import numpy as np

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "util"))
    from log import log_event
    import general_util
    import audio

    AUDIO_DIR = "/home/denial/denial_payphone/payphone/audio_files/dev"
    ROOT_DIR = "/home/denial/denial_payphone/payphone"

    session = {
        "session_id": session_id,
        "start_time": datetime.now().isoformat()
    }
    session["folder"] = general_util.create_session_folder(session_id, ROOT_DIR)
    log_event(session_id, "session_start", session["folder"])

    try:
        audio.play_audio_file("intro_prompt.wav", AUDIO_DIR)
        sd.wait()

        heard = audio.listen_for_amplitude(threshold=0.1, timeout=6)

        if heard:
            log_event(session_id, "amplitude_detected_after_intro")
            audio.play_audio_file("post_intro_user_did_speak.wav", AUDIO_DIR)
        else:
            log_event(session_id, "no_amplitude_detected_after_intro")
            audio.play_audio_file("post_intro_user_did_not_speak.wav", AUDIO_DIR)

        log_event(session_id, "session_end")
    except Exception as e:
        log_event(session_id, "session_error", str(e))
        print(f"Session {session_id} error: {e}")

if __name__ == "__main__":
    run_session("testsession")


