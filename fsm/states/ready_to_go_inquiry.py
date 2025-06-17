# fsm/states/ready_to_go_inquiry.py

from session_states import S

import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from proximity import is_on_hook
from vosk_keyword import wait_for_keyword_response


def handle_ready_to_go_inquiry(engine):
    """
    Handle the ready to go inquiry state - final prompt asking if user is ready to leave.
    
    Args:
        engine: SessionEngine instance with sensor, audio_dir, session_id, vosk_model, etc.
        
    Returns:
        S.END (always - this is the final state)
        
    Raises:
        SessionAbort: If user hangs up or audio playback fails
    """
    # Ask the user if they're ready to go
    if not play_and_log("are_you_ready_to_go.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "are you ready to go hangup"):
        raise engine.SessionAbort

    # Listen for yes/no/timeout after the prompt (single attempt, no retries)
    ready_keyword_result = wait_for_keyword_response(
        engine.vosk_model,
        on_hook_check=lambda: is_on_hook(engine.sensor)
    )

    # Handle on-hook during response
    if ready_keyword_result == "on_hook":
        print("[FSM] User hung up during ready to go inquiry")
        raise engine.SessionAbort

    # Handle affirmative response
    elif ready_keyword_result == "affirmative":
        if not play_and_log("user_agreed_to_go.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "user agreed to go hangup"):
            raise engine.SessionAbort
        if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "final disconnect hangup"):
            raise engine.SessionAbort

    # Handle negative response  
    elif ready_keyword_result == "negative":
        if not play_and_log("user_declined_to_go.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "user declined to go hangup"):
            raise engine.SessionAbort
        if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "final disconnect hangup"):
            raise engine.SessionAbort

    # Handle any other response (silence, not_understood, etc.)
    else:
        if not play_and_log("user_declined_to_go.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "user declined to go hangup"):
            raise engine.SessionAbort
        if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "timeout disconnect hangup"):
            raise engine.SessionAbort

    # All paths lead to session end
    print("[FSM] Ready to go inquiry completed - ending session")
    return S.END 