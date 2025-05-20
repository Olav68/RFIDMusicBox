import time
import json
import os

from utils import load_songs, append_log, play_song

SONGS_FILE = "/home/magic/RFIDMusicBox/songs.json"
STORAGE_DIR = "/home/magic/RFIDMusicBox/mp3"
LAST_RFID_FILE = "/home/magic/RFIDMusicBox/.last_rfid_seen.txt"

def get_last_seen():
    if os.path.exists(LAST_RFID_FILE):
        with open(LAST_RFID_FILE) as f:
            return f.read().strip()
    return None

def set_last_seen(rfid):
    with open(LAST_RFID_FILE, "w") as f:
        f.write(rfid)

print("🔁 RFID trigger-lytter kjører...")
while True:
    try:
        data = load_songs()
        rfid = data.get("last_read_rfid", "").strip()

        if not rfid or rfid == get_last_seen():
            time.sleep(1)
            continue

        append_log(f"📻 Trigger fra RFID: {rfid}")
        set_last_seen(rfid)

        for sid, song in data.items():
            if isinstance(song, dict) and song.get("rfid") == rfid:
                filepath = os.path.join(STORAGE_DIR, song["filename"])
                if os.path.exists(filepath):
                    append_log(f"▶ Spiller: {song.get('title', filepath)}")
                    play_song(filepath)
                else:
                    append_log(f"❌ Fil mangler: {filepath}")
                break

    except Exception as e:
        append_log(f"💥 Feil i trigger-lytter: {e}")
        time.sleep(2)