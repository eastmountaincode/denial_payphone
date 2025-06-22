# fsm/states/confession_inquiry.py

from session_states import S

import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from proximity import is_on_hook
from log import log_event
from vosk_keyword import wait_for_keyword_response
from config.constants import MAX_KEYWORD_ATTEMPTS, MAX_KEYWORD_SILENCE_COUNT

def handle_confession_inquiry(engine):
    """
    Handle the confession inquiry state - ask user if they're willing to confess.
    
    Args:
        engine: SessionEngine instance with sensor, audio_dir, session_id, vosk_model, etc.
        
    Returns:
        S.CONFESSION_RECORD if user agrees
        S.END if user refuses or max attempts reached
        
    Raises:
        SessionAbort: If user hangs up or audio playback fails
    """
    # Play the confession prompt
    if not play_and_log("confession_prompt_for_kw_yn.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "confession_prompt_for_kw"):
        raise engine.SessionAbort

    kw_attempts = 0
    silence_count = 0
    keyword_result = None
    
    # Keyword detection loop with retries
    while kw_attempts < MAX_KEYWORD_ATTEMPTS:
        kw_attempts += 1
        keyword_result = wait_for_keyword_response(engine.vosk_model, on_hook_check=lambda: is_on_hook(engine.sensor))
        
        if keyword_result == "on_hook":
            log_event(engine.session_id, "session_interrupted_by_on_hook", "User hung up during keyword detection.")
            raise engine.SessionAbort
            
        if keyword_result in ("affirmative", "negative"):
            log_event(engine.session_id, "keyword_result", keyword_result)
            break
            
        if keyword_result == "silence":
            silence_count += 1
            log_event(engine.session_id, "keyword_silence_detected", f"Kw Attmpt {kw_attempts}, silence count: {silence_count}")
            if silence_count == MAX_KEYWORD_SILENCE_COUNT:
                log_event(engine.session_id, "keyword_silence_detected", f"Kw Attmpt {kw_attempts}, silence count: {silence_count}")
                if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "silence disconnect"):
                    raise engine.SessionAbort
                print("[FSM]: Max silence count reached during confession inquiry - ending session")
                return S.END
            if not play_and_log("confession_kw_misunderstood_yn.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "silence occurence"):
                raise engine.SessionAbort
            continue
            
        # keyword_result == "not_understood" or other
        log_event(engine.session_id, "keyword_not_understood", f"Attempt {kw_attempts}")
        if kw_attempts == MAX_KEYWORD_ATTEMPTS:
            break
        if not play_and_log("confession_kw_misunderstood.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "keyword not understood"):
            raise engine.SessionAbort

    # Handle max attempts reached
    if kw_attempts == MAX_KEYWORD_ATTEMPTS:
        log_event(engine.session_id, "keyword_max_attempts_reached")
        if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "keyword max attempts"):
            raise engine.SessionAbort
        print("[FSM]: Max keyword attempts reached during confession inquiry - ending session")
        return S.END
    
    # Handle user response
    if keyword_result == "negative":
        if not play_and_log("confession_user_denied.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "user denied to confess hangup"):
            raise engine.SessionAbort
        if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "dscnnctd cnfssion dnial hangup"):
            raise engine.SessionAbort
        print("[FSM]: User denied confession - ending session")
        return S.END
    
    # keyword_result == "affirmative" - proceed to recording and transcription
    if keyword_result == "affirmative":
        print("[FSM]: User agreed to confess - moving to confession recording and transcription")
        return S.CONFESSION_RECORD_AND_TRANSCRIBE
    
    # Should not reach here, but safety fallback
    print("[FSM]: Unexpected keyword result - ending session")
    return S.END 