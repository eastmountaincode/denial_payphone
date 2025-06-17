import os
import wave

DIR = "/home/denial/denial_payphone/payphone/audio_files/prod_2025_06_13"

for filename in sorted(os.listdir(DIR)):
    if filename.lower().endswith(".wav"):
        path = os.path.join(DIR, filename)
        try:
            with wave.open(path, "rb") as wf:
                rate = wf.getframerate()
                if rate == 48000:
                    print(f"OK        : {filename} ({rate} Hz)")
                else:
                    print(f"NOT 48 kHz: {filename} ({rate} Hz)")
        except Exception as e:
            print(f"ERROR     : {filename} – {e}")

