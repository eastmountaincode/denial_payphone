# fsm/states/confession_record_and_transcribe.py

import os
from session_states import S

import fsm.common  # Setup paths to util directory

from general_util import play_and_log
from proximity import is_on_hook
from log import log_event
from audio import record_and_transcribe, save_audio_compressed
import soundfile as sf

# Constants from original code
VOSK_SR = 48000  # Sample rate for audio recording
MAX_SILENCE_ATTEMPTS = 2


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
    silence_attempts = 0
    
    # Recording and transcription loop with silence retry logic
    while silence_attempts < MAX_SILENCE_ATTEMPTS:
        # Play prompt that user is about to confess
        if not play_and_log("confession_user_agreed.wav", str(engine.audio_dir), engine.sensor, engine.session_id, "user is about to confess hang-up"):
            raise engine.SessionAbort

        # Start simultaneous recording and transcription
        log_event(engine.session_id, "recording_and_transcribing_confession...")
        print("FSM: Starting simultaneous recording and transcription...")
        
        status, audio_np, transcript = record_and_transcribe(
            vosk_model=engine.vosk_model,
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

        # status == "audio" - save the confession and transcript
        print(f"FSM: Recording completed. Transcript length: {len(transcript)} characters")
        
        # Save the audio file with compression
        confession_path = os.path.join(str(engine.session_folder), f"confession_{engine.session_id}.flac")
        compression_info = save_audio_compressed(audio_np, VOSK_SR, confession_path)
        
        # Log compression results
        log_event(engine.session_id, "confession_audio_saved", confession_path)
        log_event(engine.session_id, "compression_timing", {
            "total_time": f"{compression_info['total_time']:.3f}s",
            "flac_conversion_time": f"{compression_info['flac_conversion_time']:.3f}s", 
            "size_reduction": f"{compression_info['size_reduction_percent']:.1f}%",
            "original_size_mb": f"{compression_info['temp_size_bytes'] / 1024 / 1024:.1f}MB",
            "compressed_size_mb": f"{compression_info['final_size_bytes'] / 1024 / 1024:.1f}MB"
        })
        print(f"[COMPRESSION]: Total time: {compression_info['total_time']:.3f}s, Size reduction: {compression_info['size_reduction_percent']:.1f}%")
        
        # Save the transcript
        transcript_path = os.path.join(str(engine.session_folder), f"confession_transcript_{engine.session_id}.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
        log_event(engine.session_id, "confession_transcript_saved", transcript_path)
        
        print(f"FSM: Files saved - Audio: {confession_path}, Transcript: {transcript_path}")
        print(f"FSM: Transcript preview: {transcript[:100]}..." if len(transcript) > 100 else f"FSM: Full transcript: {transcript}")
        
        break

    # Move to sentiment analysis state
    print("FSM: Confession recording and transcription completed - moving to sentiment analysis")
    return S.CONFESSION_ANALYZE_SENTIMENT 