# session_fsm.py

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import os
# import soundfile as sf  # Will need this later for audio recording states

from session_states import S

# In-house libraries - same imports as original run_session.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
import sys
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from log import log_event
from audio import play_audio_file, listen_for_amplitude, record_confession
from general_util import create_session_folder, play_and_log, generate_unique_session_id 
from proximity import is_on_hook
from vosk_transcribe import vosk_transcribe
from vosk_keyword import wait_for_keyword_response

@dataclass
class SessionCtx:
    id: str
    folder: Path
    start: datetime = field(default_factory=datetime.now)
    pockets_text: str = ""
    confessed: bool = False
    gave_info: bool = False

class SessionAbort(Exception):
    """Raised for on-hook or unrecoverable errors."""
    pass

class SessionEngine:
    def __init__(self, sensor, root, audio_dir, vosk_model):
        self.sensor      = sensor
        self.root        = Path(root)
        self.audio_dir   = Path(audio_dir)
        self.vosk_model  = vosk_model

        # Generate session ID and create folder
        sid              = generate_unique_session_id(str(root))
        self.ctx         = SessionCtx(
                              id=sid,
                              folder=Path(create_session_folder(sid, str(root)))
                          )

        # State table - starting with just intro
        self.state_table = {
            S.INTRO:             self.st_intro,
            # TODO: Add other states as we implement them
            # S.POCKETS_Q:         self.st_pockets,
            # S.CONFESSION_PROMPT: self.st_conf_prompt,
            # S.CONFESS:           self.st_confess,
            # S.POST_CONF_PROMPT:  self.st_post_conf,
            # S.INFO_RECORD:       self.st_info_record,
            # S.READY_PROMPT:      self.st_ready,
        }

    # -------- public entry point --------
    # "Public entry point" - the method you call from outside the class to start the workflow
    def run(self):
        """Main FSM execution loop"""
        log_event(self.ctx.id, "session_start", str(self.ctx.folder))
        
        # Set the initial state to INTRO
        state = S.INTRO

        # Each iteration executes the handler for the current state,
        # which may block (e.g., waiting for user input), and then returns the next state.
        while state is not S.END:
            try:
                print(f"FSM: Entering state {state.name}")
                state = self.state_table[state]()
                print(f"FSM: Transitioning to state {state.name if state != S.END else 'END'}")
            except SessionAbort:
                log_event(self.ctx.id, "session_aborted")
                print("FSM: Session aborted")
                state = S.END
            except Exception as e:
                log_event(self.ctx.id, "session_error", str(e))
                print(f"FSM: Session error: {e}")
                state = S.END
        
        log_event(self.ctx.id, "session_end")
        print("FSM: Session ended")

    # -------- individual state handlers --------
    def st_intro(self):
        """Handle the intro state - play intro prompt and listen for user response"""
        # Play intro prompt
        if not play_and_log("intro_prompt.wav", str(self.audio_dir), self.sensor, self.ctx.id, "intro prompt hangup"):
            raise SessionAbort
        
        # Listen for user to say something (matching original logic)
        heard = listen_for_amplitude(
            threshold=0.05,  # LISTEN_FOR_AMPL_THRESH from original
            timeout=6, 
            is_on_hook=lambda: is_on_hook(self.sensor)
        )
        
        if heard is None:
            log_event(self.ctx.id, "session_interrupted_by_on_hook", "User hung up during listen_for_amplitude.")
            print("Session interrupted (on-hook during listen).")
            raise SessionAbort
        
        # Play appropriate response based on whether user spoke
        if heard:
            log_event(self.ctx.id, "amplitude_detected_after_intro")
            wav = "post_intro_user_did_speak.wav"
        else:
            log_event(self.ctx.id, "no_amplitude_detected_after_intro")
            wav = "post_intro_user_did_not_speak.wav"
        
        if not play_and_log(wav, str(self.audio_dir), self.sensor, self.ctx.id, "intro response hangup"):
            raise SessionAbort
        
        # For now, just end here - we'll add the next state transition later
        print("FSM: Intro state completed - ending for now")
        return S.END


# -------- Drop-in replacement function for orchestrator --------
def run_session(sensor, ROOT_DIR, AUDIO_DIR, vosk_model):
    """
    Drop-in replacement for the original run_session function.
    This allows the orchestrator to remain unchanged.
    """
    try:
        engine = SessionEngine(sensor, ROOT_DIR, AUDIO_DIR, vosk_model)
        engine.run()
    except Exception as e:
        print(f"FSM run_session error: {e}") 