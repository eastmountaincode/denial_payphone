# session_fsm.py

from pathlib import Path
import os

from session_states import S
# Import all state handlers directly
from fsm.states.intro import handle_intro
from fsm.states.pockets import handle_pockets
from fsm.states.confession_inquiry import handle_confession_inquiry
from fsm.states.confession_record_and_transcribe import handle_confession_record_and_transcribe
from fsm.states.confession_analyze_sentiment import handle_confession_analyze_sentiment
from fsm.states.post_confession_info_request import handle_post_confession_info_request
from fsm.states.post_confession_info_record import handle_post_confession_info_record
from fsm.states.ready_to_go_inquiry import handle_ready_to_go_inquiry

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UTIL_DIR = os.path.join(BASE_DIR, "util")
DATABASE_DIR = os.path.join(BASE_DIR, "database")
import sys
if UTIL_DIR not in sys.path:
    sys.path.insert(0, UTIL_DIR)
if DATABASE_DIR not in sys.path:
    sys.path.insert(0, DATABASE_DIR)

from log import log_event
from general_util import create_session_folder, generate_unique_session_id
from session_db import insert_session

class SessionAbort(Exception):
    """Raised for on-hook or unrecoverable errors."""
    pass

class SessionEngine:
    def __init__(self, sensor, root, audio_dir, vosk_model, fasttext_model):
        self.sensor      = sensor
        self.root        = Path(root)
        self.audio_dir   = Path(audio_dir)
        self.vosk_model  = vosk_model
        self.fasttext_model = fasttext_model
        
        # Make SessionAbort accessible to state handlers
        self.SessionAbort = SessionAbort

        self.session_id = generate_unique_session_id(str(root))
        #self.session_id = "session1234"
        self.session_folder = Path(create_session_folder(self.session_id, str(root)))

        # State table mapping 
        self.state_table = {
            S.INTRO: handle_intro,
            S.POCKETS_Q: handle_pockets,
            S.CONFESSION_INQUIRY: handle_confession_inquiry,
            S.CONFESSION_RECORD_AND_TRANSCRIBE: handle_confession_record_and_transcribe,
            S.CONFESSION_ANALYZE_SENTIMENT: handle_confession_analyze_sentiment,
            S.POST_CONFESSION_INFO_REQUEST: handle_post_confession_info_request,
            S.POST_CONFESSION_INFO_RECORD: handle_post_confession_info_record,
            S.READY_TO_GO_INQUIRY: handle_ready_to_go_inquiry,
        }
        print(f"FSM: Loaded {len(self.state_table)} state handlers")

    # -------- public entry point --------
    # "Public entry point" - the method you call from outside the class to start the workflow
    def run(self):
        """Main FSM execution loop"""
        log_event(self.session_id, "session_start", str(self.session_folder))
        insert_session(self.session_id)
        
        # Set the initial state to INTRO
        state = S.POST_CONFESSION_INFO_REQUEST

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
                state = S.END
            except Exception as e:
                log_event(self.session_id, "session_error", str(e))
                state = S.END
        
        log_event(self.session_id, "session_end")


def run_session(sensor, ROOT_DIR, AUDIO_DIR, vosk_model, fasttext_model):
    """
    Initialize and execute a complete payphone confession session using a finite state machine.
    
    This is the main entry point for payphone sessions, called when a user picks up the phone
    (goes off-hook).
    
    Args:
        sensor: Proximity sensor object for detecting phone on/off-hook status
        ROOT_DIR (str): Root directory path for session data storage and file operations
        AUDIO_DIR (str): Directory containing audio prompt files
        vosk_model: Pre-loaded Vosk speech recognition model for real-time transcription
        fasttext_model: Pre-loaded fastText model for sentiment analysis of confessions
    
    Returns:
        None: Function handles session completion internally and logs results
    
    Raises:
        Exception: Catches and logs any unhandled exceptions during session execution
        
    Side Effects:
        - Creates a unique session folder under ROOT_DIR/sessions/
        - Records and saves audio files (confession, user info) as compressed FLAC
        - Saves transcription text files for all recorded audio
        - May terminate early if user hangs up (detected via proximity sensor)
        
    Note:
        This function is designed to be called from the orchestrator loop after off-hook
        detection. All audio I/O operations include on-hook monitoring for graceful
        session termination if the user hangs up mid-session.
    """
    try:
        engine = SessionEngine(sensor, ROOT_DIR, AUDIO_DIR, vosk_model, fasttext_model)
        engine.run()
    except Exception as e:
        print(f"FSM run_session error: {e}") 
