import os
from datetime import datetime, timezone
from config.constants import SESSIONS_ROOT

'''
event: the main action or step - "audio_recorded"
value: optional, for "audio_recorded", it might be the path to the saved file, for example
'''
def log_event(session_id: str, event: str, value: str = None, verbose: bool = True) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    msg = f"[LOG] {timestamp} | {session_id} | {event}"
    if value is not None:
        msg += f": {value}"
    if verbose:
        print(msg)
    try:
        session_folder = os.path.join(SESSIONS_ROOT, session_id)
        os.makedirs(session_folder, exist_ok=True)
        logfile = os.path.join(session_folder, f"{session_id}_log.txt")
        with open(logfile, "a") as f:
            f.write(msg + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"LOGGING ERROR: {e} | {msg}")

