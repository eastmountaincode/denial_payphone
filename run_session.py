# run_session.py

from datetime import datetime
import os
import sys
import queue
from vosk import Model, KaldiRecognizer

# normally we invoke run_session from Orchestrator, but in case we 
# want to invoke run_session directly, this patch will facilitate that
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from log import log_event
from audio import play_audio_file, listen_for_amplitude
from general_util import create_session_folder, play_and_log, generate_unique_session_id 
from proximity import is_on_hook
from vosk_transcribe import vosk_transcribe

LISTEN_FOR_AMPL_THRESH = 0.07

VOSK_MODEL_PATH  = "/home/denial/denial_payphone/vosk/models/vosk-model-small-en-us-0.15"
VOSK_DEVICE      = 1          
VOSK_SR          = 48000
VOSK_BLOCK       = 4800
VOSK_SILENCE_BLOCKS = 30      # 3 seconds


def run_session(sensor, ROOT_DIR, AUDIO_DIR, vosk_model):
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
    session["folder"] = create_session_folder(session_id, ROOT_DIR)
    log_event(session_id, "session_start", session["folder"])

    try:
        if not play_and_log("intro_prompt.wav", AUDIO_DIR, sensor, session_id, "intro prompt"):
            return

        heard = listen_for_amplitude(threshold=LISTEN_FOR_AMPL_THRESH, timeout=6, is_on_hook=lambda: is_on_hook(sensor))
        if heard is None:
            log_event(session_id, "session_interrupted_by_on_hook", "User hung up during listen_for_amplitude.")
            print("Session interrupted (on-hook during listen).")
            return

        if heard:
            log_event(session_id, "amplitude_detected_after_intro")
            if not play_and_log("post_intro_user_did_speak.wav", AUDIO_DIR, sensor, session_id, "post-intro response"):
                return
        else:
            log_event(session_id, "no_amplitude_detected_after_intro")
            if not play_and_log("post_intro_user_did_not_speak.wav", AUDIO_DIR, sensor, session_id, "post-intro no-speak response"):
                return

        if not play_and_log("pockets_prompt.wav", AUDIO_DIR, sensor, session_id, "pockets prompt"):
            return

        log_event(session_id, "starting_transcription_1")
        transcript = vosk_transcribe(vosk_model, on_hook_check=lambda: is_on_hook(sensor))
        log_event(session_id, "transcription_result", transcript)

        if not transcript.strip():
            log_event(session_id, "pockets_no_speech_detected")
            if not play_and_log("pockets_user_did_not_respond.wav", AUDIO_DIR, sensor, session_id, "pockets no-response message"):
                return
        else:
            log_event(session_id, "pockets_user_responded", transcript)
            if not play_and_log("pockets_user_responded.wav", AUDIO_DIR, sensor, session_id, "pockets response message"):
                return
            response_path = os.path.join(session["folder"], "pockets_transcript.txt")
            with open(response_path, "w") as f:
                f.write(transcript.strip())
            log_event(session_id, "saved_transcript", response_path)

        if not play_and_log("confession_prompt_for_kw.wav", AUDIO_DIR, sensor, session_id, "confession_prompt_for_kw"):
            return

        log_event(session_id, "session_end")
    except Exception as e:
        log_event(session_id, "session_error", str(e))
        print(f"Session {session_id} error: {e}")

