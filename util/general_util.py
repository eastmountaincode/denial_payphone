import os

def create_session_folder(session_id, ROOT_DIR):
    folder_path = os.path.join(ROOT_DIR, "sessions", session_id)
    os.makedirs(folder_path, exist_ok=True)
    print(f"Created session folder: {folder_path}")
    return folder_path
