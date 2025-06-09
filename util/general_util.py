import os
import uuid

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
