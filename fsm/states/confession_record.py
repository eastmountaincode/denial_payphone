# fsm/states/confession_record.py

import os
import sys
from session_states import S

# Import utilities
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UTIL_DIR = os.path.join(BASE_DIR, "util")
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from general_util import play_and_log
from proximity import is_on_hook
from log import log_event
from audio import record_confession
import soundfile as sf

# Constants from original code
VOSK_SR = 48000  # Sample rate for audio recording
MAX_SILENCE_ATTEMPTS = 2


def handle_confession_record(engine):
    """
    Handle the confession recording state - record user's confession audio.
    
    Args:
        engine: SessionEngine instance with sensor, audio_dir, session_id, session_folder, etc.
        
    Returns:
        S.POST_CONFESSION_INFO_REQUEST if confession recorded successfully
        S.END if user hangs up or max silence attempts reached
        
    Raises:
        SessionAbort: If user hangs up or audio playback fails
    """
    silence_attempts = 0
    
    # Recording loop with silence retry logic
    while silence_attempts < MAX_SILENCE_ATTEMPTS:
        # Play prompt that user is about to confess
        if not play_and_log("confession_user_agreed.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "user is about to confess hang-up"):
            raise engine.SessionAbort

        # Start recording confession
        log_event(engine.session_id, "recording_confession...")
        status, audio_np = record_confession(
            threshold=0.05,
            on_hook_check=lambda: is_on_hook(engine.sensor)
        )

        # Handle on-hook during recording
        if status == "on_hook":
            log_event(engine.session_id, "confession_aborted_on_hook")
            raise engine.SessionAbort

        # Handle silence during recording
        if status == "silence":
            silence_attempts += 1
            log_event(engine.session_id, "confession_no_speech_detected", f"Attempt {silence_attempts}")
            if silence_attempts == MAX_SILENCE_ATTEMPTS:
                if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "cnfssion slnce dscnnet"):
                    raise engine.SessionAbort
                print("FSM: Max silence attempts reached during confession recording - ending session")
                return S.END
            # On first silence, just loop and replay the prompt
            print(f"FSM: Silence detected during confession recording, attempt {silence_attempts}/{MAX_SILENCE_ATTEMPTS}")
            continue

        # status == "audio" - save the confession
        confession_path = os.path.join(str(engine.session_folder), f"confession_{engine.session_id}.wav")
        sf.write(confession_path, audio_np, VOSK_SR)
        log_event(engine.session_id, "confession_audio_saved", confession_path)
        print(f"FSM: Confession recorded and saved to {confession_path}")
        break

    # Play post-confession message
    if not play_and_log("post_confession_message.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "post confession msg disconnect"):
        raise engine.SessionAbort

    # Move to next state - post confession info request
    print("FSM: Confession recording completed - moving to post confession info request")
    return S.POST_CONFESSION_INFO_REQUEST 