import json
import time
import os

from utils import append_log, load_songs, play_song

SONGS_FILE = "/home/magic/RFIDMusicBox/songs.json"
STORAGE_DIR = "/home/magic/RFIDMusicBox/mp3"
LAST_RFID_FILE = "/home/magic/RFIDMusicBox/.last_rfid_seen.txt"

def find_song_by_rfid(data, rfid_code):
    for key, val in data.items():
        if isinstance(val, dict) and val.get("rfid") == rfid_code:
            return val
    return None

def get_last_seen_rfid():
    if os.path.exists(LAST_RFID_FILE):
        with open(LAST_RFID_FILE, "r") as f:
            return f.read().strip()
    return None

def set_last_seen_rfid(rfid_code):
    with open(LAST_RFID_FILE, "w") as f:
        f.write(rfid_code)

def main():
    append_log("🔌 RFID-lytter er startet")
    while True:
        try:
            data = load_songs()
            current_rfid = data.get("last_read_rfid", "").strip()
            if not current_rfid:
                time.sleep(1)
                continue

            last_seen = get_last_seen_rfid()
            if current_rfid != last_seen:
                append_log(f"📻 Ny RFID skannet: {current_rfid}")
                set_last_seen_rfid(current_rfid)

                song = find_song_by_rfid(data, current_rfid)
                if song:
                    filepath = os.path.join(STORAGE_DIR, song["filename"])
                    if os.path.exists(filepath):
                        append_log(f"▶ Spiller: {song.get('title', filepath)}")
                        play_song(filepath)
                    else:
                        append_log(f"❗ MP3-fil ikke funnet: {filepath}")
                else:
                    append_log(f"🚫 Ingen sang knyttet til RFID: {current_rfid}")

            time.sleep(1)

        except Exception as e:
            append_log(f"💥 Feil i RFID-leser: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()