# fsm/states/intro.py

from session_states import S

import fsm.common  # Setup paths to util directory

from audio import listen_for_amplitude
from general_util import play_and_log
from proximity import is_on_hook
from log import log_event
import time


def handle_intro(engine):
    """
    Handle the intro state - play intro prompt and listen for user response.
    
    Args:
        engine: SessionEngine instance with sensor, audio_dir, ctx, etc.
        
    Returns:
        Next state (S.POCKETS_Q)
        
    Raises:
        SessionAbort: If user hangs up or audio playback fails
    """
    # You are being connected message
    if not play_and_log("you_are_being_connected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "being connected message"):
        raise engine.SessionAbort

    # Play intro prompt
    if not play_and_log("intro_prompt.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "intro prompt hangup"):
        raise engine.SessionAbort
    
    # Listen for user to say something
    heard = listen_for_amplitude(
        threshold=0.05,
        timeout=6, 
        is_on_hook=lambda: is_on_hook(engine.sensor)
    )
    
    if heard is None:
        log_event(engine.session_id, "session_interrupted_by_on_hook", "User hung up during listen_for_amplitude.")
        print("Session interrupted (on-hook during listen).")
        raise engine.SessionAbort
    
    # Play appropriate response based on whether user spoke
    if heard:
        log_event(engine.session_id, "amplitude_detected_after_intro")
        resp = "post_intro_user_did_speak.wav"
    else:
        log_event(engine.session_id, "no_amplitude_detected_after_intro")
        resp = "post_intro_user_did_not_speak.wav"
    
    if heard:
        time.sleep(2.0)
    if not play_and_log(resp, str(engine.audio_dir), engine.sensor, engine.session_id, "intro response hangup"):
        raise engine.SessionAbort
    
    # Transition to pockets question state
    print("[FSM]: Intro state completed - moving to pockets question")
    return S.POCKETS_Q 
