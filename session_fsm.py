# session_fsm.py

from pathlib import Path
import os
# import soundfile as sf  # Will need this later for audio recording states

from session_states import S
from fsm.state_registry import load_state_handlers

# In-house libraries - same imports as original run_session.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
import sys
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)

from log import log_event
from general_util import create_session_folder, generate_unique_session_id

class SessionAbort(Exception):
    """Raised for on-hook or unrecoverable errors."""
    pass

class SessionEngine:
    def __init__(self, sensor, root, audio_dir, vosk_model):
        self.sensor      = sensor
        self.root        = Path(root)
        self.audio_dir   = Path(audio_dir)
        self.vosk_model  = vosk_model
        
        # Make SessionAbort accessible to state handlers
        self.SessionAbort = SessionAbort

        # Generate session ID and create folder - direct attributes instead of SessionCtx
        self.session_id = generate_unique_session_id(str(root))
        self.session_folder = Path(create_session_folder(self.session_id, str(root)))

        # Load state handlers dynamically from fsm/states/ directory
        self.state_table = load_state_handlers()
        print(f"FSM: Loaded {len(self.state_table)} state handlers")

    # -------- public entry point --------
    # "Public entry point" - the method you call from outside the class to start the workflow
    def run(self):
        """Main FSM execution loop"""
        log_event(self.session_id, "session_start", str(self.session_folder))
        
        # Set the initial state to INTRO
        state = S.INTRO

        # Each iteration executes the handler for the current state,
        # which may block (e.g., waiting for user input), and then returns the next state.
        while state is not S.END:
            try:
                print(f"FSM: Entering state {state.name}")
                
                # Call the appropriate state handler, passing this engine instance
                if state in self.state_table:
                    state = self.state_table[state](self)
                else:
                    raise Exception(f"No handler found for state {state.name}")
                    
                print(f"FSM: Transitioning to state {state.name if state != S.END else 'END'}")
            except SessionAbort:
                log_event(self.session_id, "session_aborted")
                print("FSM: Session aborted")
                state = S.END
            except Exception as e:
                log_event(self.session_id, "session_error", str(e))
                print(f"FSM: Session error: {e}")
                state = S.END
        
        log_event(self.session_id, "session_end")
        print("FSM: Session ended")


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