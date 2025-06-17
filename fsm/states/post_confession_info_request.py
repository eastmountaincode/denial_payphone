# fsm/states/post_confession_info_request.py

from session_states import S

import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from proximity import is_on_hook
from log import log_event
from vosk_keyword import wait_for_keyword_response
from config.constants import MAX_KEYWORD_ATTEMPTS, MAX_KEYWORD_SILENCE_COUNT

def handle_post_confession_info_request(engine):
    """
    Handle the post confession info request state - ask if user wants to provide additional info.
    
    Args:
        engine: SessionEngine instance with sensor, audio_dir, session_id, vosk_model, etc.
        
    Returns:
        S.POST_CONFESSION_INFO_RECORD if user agrees to provide info
        S.END if user refuses or max attempts reached
        
    Raises:
        SessionAbort: If user hangs up or audio playback fails
    """
    # Play the info request prompt
    if not play_and_log("post_confession_info_request.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "post cnfssn info req dscnnct"):
        raise engine.SessionAbort

    kw_attempts = 0
    silence_count = 0
    keyword_result = None

    # Keyword detection loop for info request
    while kw_attempts < MAX_KEYWORD_ATTEMPTS:
        kw_attempts += 1
        keyword_result = wait_for_keyword_response(engine.sensor, engine.vosk_model, on_hook_check=lambda: is_on_hook(engine.sensor))

        if keyword_result == "on_hook":
            log_event(engine.session_id, "session_interrupted_by_on_hook", "User hung up during info-request keyword detection")
            raise engine.SessionAbort

        if keyword_result in ("affirmative", "negative"):
            log_event(engine.session_id, "info_request_keyword_result", keyword_result)
            break

        if keyword_result == "silence":
            silence_count += 1
            log_event(engine.session_id, "info_request_silence_detected", f"Attempt {kw_attempts}, silence {silence_count}")
            if silence_count == MAX_KEYWORD_SILENCE_COUNT:
                if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "info request silence disconnect"):
                    raise engine.SessionAbort
                print("FSM: Max silence count reached during info request - ending session")
                return S.END
            # First silence → replay the info-request prompt only
            if not play_and_log("post_confession_info_request.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "info request repeat hangup"):
                raise engine.SessionAbort
            continue

        # keyword_result == "not_understood"
        log_event(engine.session_id, "info_request_not_understood", f"Attempt {kw_attempts}")
        if kw_attempts == MAX_KEYWORD_ATTEMPTS:
            break
        if not play_and_log("info_request_misunderstood_resp.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "info request misunderstood"):
            raise engine.SessionAbort

    # Handle max attempts reached
    if kw_attempts == MAX_KEYWORD_ATTEMPTS:
        log_event(engine.session_id, "info_request_max_attempts_reached")
        if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "info request max attempts"):
            raise engine.SessionAbort
        print("FSM: Max keyword attempts reached during info request - ending session")
        return S.END

    # Handle user response
    if keyword_result == "negative":
        if not play_and_log("info_request_negative_resp.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "info request negative response hangup"):
            raise engine.SessionAbort
        if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "you are being disconnected info req hangup"):
            raise engine.SessionAbort
        print("FSM: User declined to provide info - ending session")
        return S.END

    # keyword_result == "affirmative" - proceed to info recording
    if keyword_result == "affirmative":
        if not play_and_log("info_request_affirmative_resp.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "info request affirmative response"):
            raise engine.SessionAbort
        print("FSM: User agreed to provide info - moving to info recording")
        return S.POST_CONFESSION_INFO_RECORD

    # Should not reach here, but safety fallback
    print("FSM: Unexpected keyword result in info request - ending session")
    return S.END 