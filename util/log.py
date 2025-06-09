import os
from datetime import datetime, timezone

LOG_DIR = "/home/denial/denial_payphone/logs"

'''
event: the main action or step - "audio_recorded"
value: optional, for "audio_recorded", the path to the saved file, for example
'''
def log_event(run_id: str, event: str, value: str = None) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    msg = f"{ts} | {run_id} | {event}"
    if value is not None:
        msg += f": {value}"
    print(msg)
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        logfile = os.path.join(LOG_DIR, f"log_{datetime.now(timezone.utc).date()}.txt")
        with open(logfile, "a") as f:
            f.write(msg + "\n")
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"LOGGING ERROR: {e} | {msg}")
