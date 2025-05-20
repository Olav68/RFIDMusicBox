import json
import time
import os
import subprocess

SONGS_FILE = "/home/magic/RFIDMusicBox/songs.json"
#MUSIC_DIR = "/home/magic/RFIDMusicBox/music"
STORAGE_DIR = "/home/magic/RFIDMusicBox/mp3"
LAST_RFID_FILE = "/home/magic/RFIDMusicBox/.last_rfid_seen.txt"

def load_songs():
    with open(SONGS_FILE, "r") as f:
        return json.load(f)

def find_song_by_rfid(data, rfid_code):
    for key, val in data.items():
        if isinstance(val, dict) and val.get("rfid") == rfid_code:
            return val
    return None

def stop_audio():
    subprocess.call(["pkill", "mpv"])

def play_audio(filepath):
    subprocess.Popen(["mpv", "--no-video", filepath])

def beep_error():
    # Dobbel pip
    subprocess.call(["speaker-test", "-t", "sine", "-f", "1000", "-l", "1", "-P", "1", "-p", "100"])
    time.sleep(0.1)
    subprocess.call(["speaker-test", "-t", "sine", "-f", "1000", "-l", "1", "-P", "1", "-p", "100"])

def get_last_seen_rfid():
    if os.path.exists(LAST_RFID_FILE):
        with open(LAST_RFID_FILE, "r") as f:
            return f.read().strip()
    return None

def set_last_seen_rfid(rfid_code):
    with open(LAST_RFID_FILE, "w") as f:
        f.write(rfid_code)

def main():
    print("🎧 RFID-lytter er startet...")
    while True:
        try:
            data = load_songs()
            current_rfid = data.get("last_read_rfid", "").strip()
            if not current_rfid:
                time.sleep(1)
                continue

            last_seen = get_last_seen_rfid()
            if current_rfid != last_seen:
                print(f"📻 Ny RFID skannet: {current_rfid}")
                set_last_seen_rfid(current_rfid)

                song = find_song_by_rfid(data, current_rfid)
                if song:
                    filepath = os.path.join(MUSIC_DIR, song["filename"])
                    if os.path.exists(filepath):
                        print(f"▶ Spiller: {song['title']}")
                        stop_audio()
                        play_audio(filepath)
                    else:
                        print(f"❗ MP3-fil ikke funnet: {filepath}")
                        beep_error()
                else:
                    print("🚫 Ingen sang knyttet til denne RFID-koden.")
                    beep_error()
            time.sleep(1)

        except Exception as e:
            print(f"💥 Feil oppstod: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()