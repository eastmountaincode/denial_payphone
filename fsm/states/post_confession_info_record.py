# fsm/states/post_confession_info_record.py

import os
from session_states import S

import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from proximity import is_on_hook
from log import log_event
from audio import record_and_transcribe, save_audio_compressed
from config.constants import MAX_RECORDING_SILENCE_COUNT

def handle_post_confession_info_record(engine):
    """
    Handle the post confession info recording state - record
      additional user information like email or instagram handle.
    
    Args:
        engine: SessionEngine instance with sensor, audio_dir, session_id, session_folder, etc.
        
    Returns:
        S.READY_TO_GO_INQUIRY if info recorded successfully
        S.END if user hangs up or max silence attempts reached
        
    Raises:
        SessionAbort: If user hangs up or audio playback fails
    """
    silence_count = 0
    
    # Info recording loop with silence retry logic
    while silence_count < MAX_RECORDING_SILENCE_COUNT:
        # Start recording and transcribing user info
        log_event(engine.session_id, "recording_and_transcribing_user_info...")
        status, audio_np, transcript = record_and_transcribe(
            vosk_model=engine.vosk_model,
            on_hook_check=lambda: is_on_hook(engine.sensor)
        )

        # Handle on-hook during recording
        if status == "on_hook":
            log_event(engine.session_id, "info_record_aborted_on_hook")
            raise engine.SessionAbort

        # Handle silence during recording
        if status == "silence":
            silence_count += 1
            log_event(engine.session_id, "info_record_silence", f"Attempt {silence_count}")
            if silence_count == MAX_RECORDING_SILENCE_COUNT:
                if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "info record silence disconnect"):
                    raise engine.SessionAbort
                print("[FSM]: Max silence attempts reached during info recording - ending session")
                return S.END
            # On silence, replay the info prompt
            if not play_and_log("info_request_affirmative_resp.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "info prompt repeat"):
                raise engine.SessionAbort
            print(f"[FSM]: Silence detected during info recording, attempt {silence_count}/{MAX_RECORDING_SILENCE_COUNT}")
            continue  # retry

        # status == "audio" - save the info recording and transcript with compression
        info_path = os.path.join(str(engine.session_folder), f"info_{engine.session_id}.flac")
        save_audio_compressed(audio_np, info_path)
        log_event(engine.session_id, "info_audio_saved", info_path)
        
        # Save the transcript
        info_transcript_path = os.path.join(str(engine.session_folder), f"info_transcript_{engine.session_id}.txt")
        with open(info_transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        log_event(engine.session_id, "info_transcript_saved", info_transcript_path)

        break  # finished recording

    # Move to next state - ready to go inquiry
    print("[FSM]: Info recording completed - moving to ready to go inquiry")
    return S.READY_TO_GO_INQUIRY 