import os
import uuid
from audio import play_audio_file
from proximity import is_on_hook
from log import log_event

def create_session_folder(session_id, ROOT_DIR):
    folder_path = os.path.join(ROOT_DIR, "sessions", session_id)
    os.makedirs(folder_path, exist_ok=True)
    print(f"Created session folder: {folder_path}")
    return folder_path

def generate_unique_session_id(ROOT_DIR):
    """
    Returns a unique session_id string (session_<8hex>) that does not already exist
    in ROOT_DIR/sessions/.
    """
    sessions_root = os.path.join(ROOT_DIR, "sessions")
    while True:
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        session_folder = os.path.join(sessions_root, session_id)
        if not os.path.exists(session_folder):
            return session_id

def play_and_log(audio_file, audio_dir, sensor, session_id, interrupt_reason):
    finished = play_audio_file(audio_file, audio_dir, lambda: is_on_hook(sensor))
    if not finished:
        log_event(session_id, "session_interrupted_by_on_hook", interrupt_reason)
        print(f"Session interrupted (on-hook during audio I/O).")
        return False
    return True

