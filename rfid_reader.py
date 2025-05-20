import json
import os
import time
from utils import append_log

SONGS_FILE = "/home/magic/RFIDMusicBox/songs.json"

def read_rfid():
    try:
        with open("/dev/ttyUSB0", "r") as reader:
            while True:
                tag = reader.readline().strip()
                if tag:
                    log_and_store_rfid(tag)
    except Exception as e:
        append_log(f"❌ RFID-leserfeil: {e}")

def log_and_store_rfid(rfid):
    append_log(f"📡 Lest RFID: {rfid}")  # <-- Her logger vi at en brikke er lest
    try:
        if os.path.exists(SONGS_FILE):
            with open(SONGS_FILE, "r") as f:
                songs = json.load(f)
        else:
            songs = {}

        songs["last_read_rfid"] = rfid

        with open(SONGS_FILE, "w") as f:
            json.dump(songs, f, indent=2)

    except Exception as e:
        append_log(f"❌ Feil ved skriving til songs.json: {e}")

if __name__ == "__main__":
    append_log("▶ Starter RFID-leser")
    read_rfid()