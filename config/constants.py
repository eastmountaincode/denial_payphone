######## Directories #########
ROOT_DIR = "/home/denial/denial_payphone/payphone"
AUDIO_DIR = "/home/denial/denial_payphone/payphone/audio_files/prod_2025_06_22"
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
MAX_KEYWORD_ATTEMPTS = 6
MAX_KEYWORD_SILENCE_COUNT = 3
MAX_RECORDING_SILENCE_COUNT = 3
KEYWORD_SILENCE_TIMEOUT_SEC = 10
SPEECH_END_PAUSE_SEC = 2.3  # How long to wait after speech ends before transitioning states
MAX_INITIAL_SILENCE_SEC = 13.0  # Max silence before prompting again or disconnecting when recording user long-form speech
AUDIO_SILENCE_THRESHOLD = 0.02  # RMS amplitude below this is considered silence (0.0-1.0)

######## Proximity sensor constants #########
PROXIMITY_THRESHOLD = 800       # >= this is ON HOOK; < this is OFF HOOK
OFF_HOOK_REQUIRED_DURATION = 3.0  # seconds proximity must stay low to count as off-hook
ON_HOOK_REQUIRED_DURATION = 8.0   # seconds proximity must stay high to count as on-hook
POLL_INTERVAL = 0.1               # seconds between sensor polls






