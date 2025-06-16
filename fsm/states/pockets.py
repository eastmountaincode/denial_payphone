# fsm/states/pockets.py

import os
from session_states import S
import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from proximity import is_on_hook
from log import log_event
from vosk_transcribe import vosk_transcribe


def handle_pockets(engine):
    """
    Handle the pockets question state - ask user what's in their pockets and transcribe response.
    
    Args:
        engine: SessionEngine instance with sensor, audio_dir, ctx, vosk_model, etc.
        
    Returns:
        Next state (S.END for now, later S.CONFESSION_PROMPT)
        
    Raises:
        SessionAbort: If user hangs up or audio playback fails
    """
    # Play the pockets prompt
    if not play_and_log("pockets_prompt.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "pockets prompt"):
        raise engine.SessionAbort

    # Start transcription
    log_event(engine.session_id, "starting_transcription_1")
    transcript = vosk_transcribe(engine.vosk_model, on_hook_check=lambda: is_on_hook(engine.sensor))
    log_event(engine.session_id, "transcription_result", transcript)
    print(f"FSM: Transcribed pockets response: '{transcript}'")

    # Handle empty vs non-empty responses
    if not transcript.strip():
        log_event(engine.session_id, "pockets_no_speech_detected")
        if not play_and_log("pockets_user_did_not_respond.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "pockets no-response message"):
            raise engine.SessionAbort
    else:
        log_event(engine.session_id, "pockets_user_responded", transcript)
        if not play_and_log("pockets_user_responded.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "pockets response message"):
            raise engine.SessionAbort
        
        # Save transcript to file (no need to store in memory since we don't use it later)
        response_path = os.path.join(str(engine.session_folder), "pockets_transcript.txt")
        with open(response_path, "w") as f:
            f.write(transcript.strip())
        log_event(engine.session_id, "saved_transcript", response_path)

    # Move to confession inquiry state
    print("FSM: Pockets state completed - moving to confession inquiry")
    return S.CONFESSION_INQUIRY 