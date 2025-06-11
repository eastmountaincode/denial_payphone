# run_session.py

from datetime import datetime
import os
import sys
import queue
from vosk import Model, KaldiRecognizer
import time
import soundfile as sf

# normally we invoke run_session from Orchestrator, but in case we 
# want to invoke run_session directly, this patch will facilitate that
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from log import log_event
from audio import play_audio_file, listen_for_amplitude, record_confession
from general_util import create_session_folder, play_and_log, generate_unique_session_id 
from proximity import is_on_hook
from vosk_transcribe import vosk_transcribe
from pv_keyword import wait_for_keyword_response

LISTEN_FOR_AMPL_THRESH = 0.04

VOSK_MODEL_PATH  = "/home/denial/denial_payphone/vosk/models/vosk-model-small-en-us-0.15"
VOSK_DEVICE      = 1          
VOSK_SR          = 48000
VOSK_BLOCK       = 4800
VOSK_SILENCE_BLOCKS = 30      # 3 seconds

MAX_KEYWORD_ATTEMPTS = 5
MAX_SILENCE_COUNT = 2

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
#        if not play_and_log("intro_prompt.wav", AUDIO_DIR, sensor, session_id, "intro prompt hangup"):
#            return
#
#        heard = listen_for_amplitude(threshold=LISTEN_FOR_AMPL_THRESH, timeout=6, is_on_hook=lambda: is_on_hook(sensor))
#        if heard is None:
#            log_event(session_id, "session_interrupted_by_on_hook", "User hung up during listen_for_amplitude.")
#            print("Session interrupted (on-hook during listen).")
#            return
#
#        if heard:
#            log_event(session_id, "amplitude_detected_after_intro")
#            if not play_and_log("post_intro_user_did_speak.wav", AUDIO_DIR, sensor, session_id, "intro response hangup"):
#                return
#        else:
#            log_event(session_id, "no_amplitude_detected_after_intro")
#            if not play_and_log("post_intro_user_did_not_speak.wav", AUDIO_DIR, sensor, session_id, "intro n-spk rspnse hangup"):
#                return
#
#        if not play_and_log("pockets_prompt.wav", AUDIO_DIR, sensor, session_id, "pockets prompt"):
#            return
#
#        log_event(session_id, "starting_transcription_1")
#        transcript = vosk_transcribe(vosk_model, on_hook_check=lambda: is_on_hook(sensor))
#        log_event(session_id, "transcription_result", transcript)
#
#        if not transcript.strip():
#            log_event(session_id, "pockets_no_speech_detected")
#            if not play_and_log("pockets_user_did_not_respond.wav", AUDIO_DIR, sensor, session_id, "pockets no-response message"):
#                return
#        else:
#            log_event(session_id, "pockets_user_responded", transcript)
#            if not play_and_log("pockets_user_responded.wav", AUDIO_DIR, sensor, session_id, "pockets response message"):
#                return
#            response_path = os.path.join(session["folder"], "pockets_transcript.txt")
#            with open(response_path, "w") as f:
#                f.write(transcript.strip())
#            log_event(session_id, "saved_transcript", response_path)
# 
#         
#         if not play_and_log("confession_prompt_for_kw.wav", AUDIO_DIR, sensor, session_id, "confession_prompt_for_kw"):
#             return
# 
#         kw_attempts = 0
#         silence_count = 0
#         while kw_attempts < MAX_KEYWORD_ATTEMPTS:
#             kw_attempts += 1
#             keyword_result = wait_for_keyword_response(sensor, on_hook_check=lambda: is_on_hook(sensor))
#             if keyword_result == "on_hook":
#                 log_event(session_id, "session_interrupted_by_on_hook", "User hung up during keyword detection.") 
#                 return
#             if keyword_result in ("affirmative", "negative"): 
#                 log_event(session_id, "keyword_result", keyword_result)
#                 break
#             if keyword_result == "silence":
#                 silence_count += 1
#                 log_event(session_id, "keyword_silence_detected", f"Kw Attmpt {kw_attempts}, silence count: {silence_count}")
#                 if silence_count == MAX_SILENCE_COUNT:
#                     log_event(session_id, "keyword_silence_detected", f"Kw Attmpt {kw_attempts}, silence count: {silence_count}")
#                     if not play_and_log("you_are_being_disconnected.wav", AUDIO_DIR, sensor, session_id, "silence disconnect"): 
#                         return
#                     return
#                 if not play_and_log("confession_kw_misunderstood.wav", AUDIO_DIR, sensor, session_id, "silence occurence"):
#                     return
#                 continue
#             log_event(session_id, "keyword_not_understood", f"Attempt {kw_attempts}")
#             if kw_attempts == MAX_KEYWORD_ATTEMPTS: 
#                 break
#             if not play_and_log("confession_kw_misunderstood.wav", AUDIO_DIR, sensor, session_id, "keyword not understood"): 
#                 return
# 
#         # Max keyword attempts reached...
#         if kw_attempts == MAX_KEYWORD_ATTEMPTS:
#             log_event(session_id, "keyword_max_attempts_reached")
#             if not play_and_log("you_are_being_disconnected.wav", AUDIO_DIR, sensor, session_id, "keyword max attempts"):
#                 return
#             return
#         
#         # -----------------------------------------------------------------
#         # NEGATIVE → DISCONNECT
#         # -----------------------------------------------------------------
#         if keyword_result == "negative":
#             if not play_and_log("confession_user_denied.wav", AUDIO_DIR, sensor, session_id, "user denied to confess hangup"):
#                 return
#             if not play_and_log("you_are_being_disconnected.wav", AUDIO_DIR, sensor, session_id, "dscnnctd cnfssion dnial hangup"):
#                 return
#             return
# 
#         # -----------------------------------------------------------------
#         # AFFIRMATIVE → RECORD CONFESSION
#         # -----------------------------------------------------------------
#         keyword_result = "affirmative"
#         if keyword_result != "affirmative":
#             print("Something is wrong")
# 
#         silence_attempts = 0
#         while silence_attempts < 2:
#             if not play_and_log("confession_user_agreed.wav", AUDIO_DIR, sensor, session_id, "user is about to confess hang-up"):
#                 return
# 
#             time.sleep(0.25)
#                 
#             log_event(session_id, "recording_confession...")
#             status, audio_np = record_confession(
#                 threshold=LISTEN_FOR_AMPL_THRESH,
#                 on_hook_check=lambda: is_on_hook(sensor)
#             )
# 
#             if status == "on_hook":
#                 log_event(session_id, "confession_aborted_on_hook")
#                 return
# 
#             if status == "silence":
#                 silence_attempts += 1
#                 log_event(session_id, "confession_no_speech_detected", f"Attempt {silence_attempts}")
#                 if silence_attempts == 2:
#                     if not play_and_log("you_are_being_disconnected.wav", AUDIO_DIR, sensor, session_id, "cnfssion slnce dscnnet"):
#                         return
#                     return
#                 # On first silence, just loop and replay the prompt
#                 continue
# 
#             # status == "audio" – save it
#             confession_path = os.path.join(session["folder"], f"confession_{session_id}.wav")
#             sf.write(confession_path, audio_np, VOSK_SR)
#             log_event(session_id, "confession_audio_saved", confession_path)
#             break
# 
#         if not play_and_log("post_confession_message.wav", AUDIO_DIR, sensor, session_id, "post confession msg disconnect"):
#             return
#         if not play_and_log("post_confession_info_request.wav", AUDIO_DIR, sensor, session_id, "post cnfssn info req dscnnct"):
#             return

        # -----------------------------------------------------------------
        # YES / NO keyword loop for post-confession user info
        # -----------------------------------------------------------------
        kw_attempts   = 0
        silence_count = 0
        keyword_result = None

        while kw_attempts < MAX_KEYWORD_ATTEMPTS:
            kw_attempts += 1
            keyword_result = wait_for_keyword_response(sensor,
                                               on_hook_check=lambda: is_on_hook(sensor))

            if keyword_result == "on_hook":
                log_event(session_id, "session_interrupted_by_on_hook",
                  "User hung up during info-request keyword detection")
                return

            if keyword_result in ("affirmative", "negative"):
                log_event(session_id, "info_request_keyword_result", keyword_result)
                break

            if keyword_result == "silence":
                silence_count += 1
                log_event(session_id, "info_request_silence_detected",
                  f"Attempt {kw_attempts}, silence {silence_count}")
                if silence_count == MAX_SILENCE_COUNT:
                    play_and_log("you_are_being_disconnected.wav", AUDIO_DIR, sensor,
                         session_id, "info request silence disconnect")
                    return
                # first silence → replay the info-request prompt only
                if not play_and_log("post_confession_info_request.wav", AUDIO_DIR, sensor,
                            session_id, "info request repeat hangup"): 
                    return
                continue

            # keyword_result == "not_understood"
            log_event(session_id, "info_request_not_understood", f"Attempt {kw_attempts}")
            if kw_attempts == MAX_KEYWORD_ATTEMPTS: break
            if not play_and_log("info_request_misunderstood_resp.wav", AUDIO_DIR, sensor,
                        session_id, "info request misunderstood"): return

        # -----------------------------------------------------------------
        # max attempts reached
        # -----------------------------------------------------------------
        if kw_attempts == MAX_KEYWORD_ATTEMPTS:
            log_event(session_id, "info_request_max_attempts_reached")
            play_and_log("you_are_being_disconnected.wav", AUDIO_DIR, sensor,
                 session_id, "info request max attempts")
            return

        # -----------------------------------------------------------------
        # branch on affirmative / negative
        # -----------------------------------------------------------------
        if keyword_result == "affirmative":
            if not play_and_log("info_request_affirmative_resp.wav", AUDIO_DIR, sensor,
                 session_id, "info request affirmative response"):
                return
        elif keyword_result == "negative":
            if not play_and_log("info_request_negative_resp.wav", AUDIO_DIR, sensor,
                 session_id, "info request negative response hangup"):
                return
            if not play_and_log("you_are_being_disconnected.wav", AUDIO_DIR, sensor,
                 session_id, "you are being disconnected info req hangup"):
                return
            return

        # -----------------------------------------------------------------
        # (only reached if affirmative) – record user info
        # -----------------------------------------------------------------
        silence_count = 0
        while silence_count < MAX_SILENCE_COUNT:
            time.sleep(0.25)  # brief gap after affirmative prompt

            status, audio_np = record_confession(
                threshold=LISTEN_FOR_AMPL_THRESH,
                on_hook_check=lambda: is_on_hook(sensor)
            )

            if status == "on_hook":
                log_event(session_id, "info_record_aborted_on_hook")
                return

            if status == "silence":
                silence_count += 1
                log_event(session_id, "info_record_silence", f"Attempt {silence_count}")
                if silence_count == MAX_SILENCE_COUNT:
                    if not play_and_log("you_are_being_disconnected.wav", AUDIO_DIR, sensor,
                                 session_id, "info record silence disconnect"):
                        return
                    return
                if not play_and_log("info_request_affirmative_resp.wav", AUDIO_DIR, sensor,
                                    session_id, "info prompt repeat"):
                    return
                continue  # retry

            # status == "audio": save it
            info_path = os.path.join(session["folder"], f"info_{session_id}.wav")
            sf.write(info_path, audio_np, VOSK_SR)
            log_event(session_id, "info_audio_saved", info_path)
            break  # finished recording

        if not play_and_log("are_you_ready_to_go.wav", AUDIO_DIR, sensor, session_id, "are you ready to go hangup"):
            return

        # final disconnect prompt
        if not play_and_log("you_are_being_disconnected.wav", AUDIO_DIR, sensor, session_id, "confession complete disconnect"):
            return
        return

    except Exception as e:
        log_event(session_id, "session_error", str(e))
        print(f"Session {session_id} error: {e}")
    finally:
        log_event(session_id, "session_end")
