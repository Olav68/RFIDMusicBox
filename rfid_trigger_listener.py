#rfid_trigger_listener
import time
import json
import os
from utils import load_songs, append_log, play_song

SONGS_FILE = "/home/magic/programmer/RFIDMusicBox/songs.json"
STORAGE_DIR = "/home/magic/programmer/RFIDMusicBox/mp3"
LAST_RFID_FILE = "/home/magic/programmer/RFIDMusicBox/.last_rfid_seen.txt"

def get_last_seen_rfid():
    append_log(f"📥 Henter siste scannede kode: {rfid}")
    if os.path.exists(LAST_RFID_FILE):
        with open(LAST_RFID_FILE, "r") as f:
            return f.read().strip()
    return None

def set_last_seen_rfid(rfid_code):
    append_log(f"📥 Setter siste scannede kode: {rfid}")
    with open(LAST_RFID_FILE, "w") as f:
        f.write(rfid_code)

def find_song_by_rfid(data, rfid_code):
    append_log(f"📥 RFID-kode mottatt: {rfid}, finnner sangen")
    for key, val in data.items():
        if isinstance(val, dict) and val.get("rfid") == rfid_code:
            return val
    return None

def main():
    append_log("🔌 RFID trigger-lytter startet")
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
                        append_log(f"❌ Fil mangler: {filepath}")
                else:
                    append_log(f"🚫 Ingen sang knyttet til RFID: {current_rfid}")

            time.sleep(1)

        except Exception as e:
            append_log(f"💥 Feil i RFID trigger-lytter: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
