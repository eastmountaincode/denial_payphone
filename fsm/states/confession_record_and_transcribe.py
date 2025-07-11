# fsm/states/confession_record_and_transcribe.py

import os
from session_states import S

import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from proximity import is_on_hook
from log import log_event
from audio import record_and_transcribe, save_audio_compressed
import soundfile as sf
from config.constants import MAX_RECORDING_SILENCE_COUNT

def handle_confession_record_and_transcribe(engine):
    """
    Handle the confession recording and transcription state - simultaneously record 
    user's confession audio and transcribe it in real-time.
    
    Args:
        engine: SessionEngine instance with sensor, audio_dir, session_id, session_folder, vosk_model, etc.
        
    Returns:
        S.POST_CONFESSION_INFO_REQUEST if confession recorded and transcribed successfully
        S.END if user hangs up or max silence attempts reached
        
    Raises:
        SessionAbort: If user hangs up or audio playback fails
    """
    silence_count = 0
    
    # Recording and transcription loop with silence retry logic
    while silence_count < MAX_RECORDING_SILENCE_COUNT:
        # Play prompt that user is about to confess
        if not play_and_log("confession_user_agreed.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "user is about to confess hang-up"):
            raise engine.SessionAbort

        # Start simultaneous recording and transcription
        log_event(engine.session_id, "recording_and_transcribing_confession...")
        print("[FSM]: Starting simultaneous recording and transcription...")
        
        status, audio_np, transcript = record_and_transcribe(
            vosk_model=engine.vosk_model,
            on_hook_check=lambda: is_on_hook(engine.sensor)
        )

        # Handle on-hook during recording
        if status == "on_hook":
            log_event(engine.session_id, "confession_aborted_on_hook")
            raise engine.SessionAbort

        # Handle silence during recording
        if status == "silence":
            silence_count += 1
            log_event(engine.session_id, "confession_no_speech_detected", f"Attempt {silence_count}")
            if silence_count == MAX_RECORDING_SILENCE_COUNT:
                if not play_and_log("you_are_being_disconnected.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "cnfssion slnce dscnnet"):
                    raise engine.SessionAbort
                print("[FSM]: Max silence attempts reached during confession recording - ending session")
                return S.END
            # On first silence, just loop and replay the prompt
            print(f"[FSM]: Silence detected during confession recording, attempt {silence_count}/{MAX_RECORDING_SILENCE_COUNT}")
            continue

        # status == "audio" - save the confession and transcript
        print(f"[FSM]: Recording completed. Transcript: {transcript} ")
        
        # Save the audio file with compression
        confession_path = os.path.join(str(engine.session_folder), f"confession_{engine.session_id}.flac")
        save_audio_compressed(audio_np, confession_path)
        log_event(engine.session_id, "confession_audio_saved", confession_path)
        
        # Save the transcript
        transcript_path = os.path.join(str(engine.session_folder), f"confession_transcript_{engine.session_id}.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        log_event(engine.session_id, "confession_transcript_saved", transcript_path)
        
        break

    # Move to sentiment analysis state
    print("[FSM]: Confession recording and transcription completed - moving to sentiment analysis")
    return S.CONFESSION_ANALYZE_SENTIMENT 