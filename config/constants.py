######## Directories #########
ROOT_DIR = "/home/denial/denial_payphone/payphone"
AUDIO_DIR = "/home/denial/denial_payphone/payphone/audio_files/prod_2025_06_13"

VOSK_MODEL_PATH  = "/home/denial/denial_payphone/vosk/models/vosk-model-small-en-us-0.15"
FASTTEXT_MODEL_PATH = "/home/denial/denial_payphone/fasttext/crawl-80d-2M-subword.bin"

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






