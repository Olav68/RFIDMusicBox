import time
import json
import os
import subprocess

SONGS_FILE = "/home/magic/RFIDMusicBox/songs.json"
STORAGE_DIR = "/home/magic/RFIDMusicBox/mp3"
LAST_RFID_FILE = "/home/magic/RFIDMusicBox/.last_rfid_seen.txt"

def load_songs():
    with open(SONGS_FILE, "r") as f:
        return json.load(f)

def get_last_seen():
    if os.path.exists(LAST_RFID_FILE):
        with open(LAST_RFID_FILE) as f:
            return f.read().strip()
    return None

def set_last_seen(rfid):
    with open(LAST_RFID_FILE, "w") as f:
        f.write(rfid)

def play_song(filepath):
    subprocess.call(["pkill", "-f", "mpv"])
    subprocess.Popen(["mpv", "--no-video", "--force-window=no", filepath])

print("🔁 RFID trigger-lytter kjører...")
while True:
    try:
        data = load_songs()
        rfid = data.get("last_read_rfid", "").strip()
        if not rfid or rfid == get_last_seen():
            time.sleep(1)
            continue

        print(f"📻 Trigger fra RFID: {rfid}")
        set_last_seen(rfid)

        for sid, song in data.items():
            if isinstance(song, dict) and song.get("rfid") == rfid:
                filepath = os.path.join(STORAGE_DIR, song["filename"])
                if os.path.exists(filepath):
                    print(f"▶ Spiller: {song['title']}")
                    play_song(filepath)
                else:
                    print(f"❌ Fil mangler: {filepath}")
                break
    except Exception as e:
        print(f"💥 Feil: {e}")
        time.sleep(2)