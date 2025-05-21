import os
import json
import subprocess
from datetime import datetime
from evdev import InputDevice, categorize, ecodes, list_devices
from utils import append_log, load_songs

SONGS_FILE = "/home/magic/programmer/RFIDMusicBox/songs.json"
STORAGE_DIR = "/home/magic/programmer/RFIDMusicBox/mp3"
DEVICE_NAME = "RFIDeas USB Keyboard"

def find_device():
    print("🔍 Søker etter input-enheter...")
    for path in list_devices():
        device = InputDevice(path)
        print(f"➡️  Fant: {device.name} @ {path}")
        if DEVICE_NAME in device.name:
            print(f"✅ Bruker {device.name} @ {path}")
            return device
    print("❌ Fant ingen enhet som matcher DEVICE_NAME")
    return None

def play_song(filepath):
    append_log(f" Spiller av: {song.get('title', sid)}")
    if not os.path.exists(filepath):
        append_log(f"❌ Fil ikke funnet: {filepath}")
        return

    subprocess.call(["pkill", "-f", "mpv"])  # Stopp forrige avspilling

    try:
        subprocess.Popen(["mpv", "--no-video", "--force-window=no", filepath])
        append_log(f"▶ Starter avspilling: {filepath}")
    except Exception as e:
        append_log(f"❌ Feil ved avspilling: {e}")

if __name__ == "__main__":
    append_log("🔌 Starter RFID-lytter")

    device = find_device()
    if not device:
        append_log("❌ Fant ikke RFID-leser")
        exit(1)

    append_log(f"✅ Leser: {device.name}")

    buffer = ""
    for event in device.read_loop():
        if event.type == ecodes.EV_KEY:
            key_event = categorize(event)
            if key_event.keystate == key_event.key_down:
                keycode = key_event.keycode
                if isinstance(keycode, list):
                    keycode = keycode[0]
                char = keycode.replace("KEY_", "")

                if char == "ENTER":
                    rfid = buffer
                    buffer = ""
                    append_log(f"📻 RFID skannet: {rfid}")

                    songs = load_songs()
                    found = False
                    for sid, song in songs.items():
                        if isinstance(song, dict) and song.get("rfid") == rfid:
                            filename = song.get("filename")
                            if not filename:
                                append_log(f"❌ Ingen filnavn for sang: {song.get('title', sid)}")
                                break
                            filepath = os.path.join(STORAGE_DIR, filename)
                            append_log(f"▶ Spiller: {song.get('title', sid)} ({filepath})")
                            play_song(filepath)
                            found = True
                            break
                    if not found:
                        append_log("❌ Ingen sang funnet for denne RFID-koden.")
                else:
                    if len(char) == 1 and char.isalnum():
                        buffer += char