######## Directories #########
ROOT_DIR = "/home/denial/denial_payphone/payphone"
AUDIO_DIR = "/home/denial/denial_payphone/payphone/audio_files/prod_2025_06_13"
SESSIONS_ROOT = "/home/denial/denial_payphone/payphone/sessions"
DATABASE_DIR = "/home/denial/denial_payphone/payphone/database"

######## Model paths #########
VOSK_MODEL_PATH  = "/home/denial/denial_payphone/vosk/models/vosk-model-small-en-us-0.15"
FASTTEXT_MODEL_PATH = "/home/denial/denial_payphone/fasttext/crawl-80d-2M-subword.bin"
PROXIMITY_MODEL_PATH = "/home/denial/denial_payphone/proximity/proximity_model.pkl"

######## Audio device indices #########
AUDIO_DEVICE_OUT_INDEX = 1 
AUDIO_DEVICE_IN_INDEX = 1  

######## Audio constants #########
AUDIO_IN_SAMPLE_RATE = 48000      # Recording sample rate (hardware native)
AUDIO_OUT_SAMPLE_RATE = 48000     # Playback sample rate
AUDIO_SAVE_SAMPLE_RATE = 48000    # Saving sample rate

######## Audio in constants #########
MAX_KEYWORD_ATTEMPTS = 4
MAX_KEYWORD_SILENCE_COUNT = 2
MAX_RECORDING_SILENCE_COUNT = 2
KEYWORD_SILENCE_TIMEOUT_SEC = 8

######## Proximity sensor constants #########
PROXIMITY_THRESHOLD = 200       # >= this is ON HOOK; < this is OFF HOOK
OFF_HOOK_REQUIRED_DURATION = 2.0  # seconds proximity must stay low to count as off-hook
ON_HOOK_REQUIRED_DURATION = 2.0   # seconds proximity must stay high to count as on-hook
POLL_INTERVAL = 0.1               # seconds between sensor polls






