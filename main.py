# main.py – Lytter til RFID og spiller sang eller spilleliste via utils.play_song
import os
from evdev import InputDevice, categorize, ecodes, list_devices
from utils import append_log, load_songs, play_song

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
                            # Spilleliste
                            if "playlist_dir" in song:
                                folder = os.path.join(STORAGE_DIR, song["playlist_dir"])
                                if os.path.exists(folder):
                                    files = sorted(f for f in os.listdir(folder) if f.endswith(".mp3"))
                                    if files:
                                        append_log(f"▶ Spiller spilleliste: {song.get('title', sid)}")
                                        for file in files:
                                            filepath = os.path.join(folder, file)
                                            append_log(f"▶ Spiller fra liste: {filepath}")
                                            play_song(filepath)
                                    else:
                                        append_log(f"❌ Ingen lydfiler i spilleliste-mappen: {folder}")
                                else:
                                    append_log(f"❌ Spilleliste-mappe finnes ikke: {folder}")
                            # Enkeltsang
                            elif "filename" in song:
                                filepath = os.path.join(STORAGE_DIR, song["filename"])
                                if os.path.exists(filepath):
                                    append_log(f"▶ Spiller: {song.get('title', sid)} ({filepath})")
                                    play_song(filepath)
                                else:
                                    append_log(f"❌ Fil ikke funnet: {filepath}")
                            else:
                                append_log(f"❌ Ingen gyldig kilde for RFID: {rfid}")
                            found = True
                            break
                    if not found:
                        append_log("❌ Ingen sang funnet for denne RFID-koden.")
                else:
                    if len(char) == 1 and char.isalnum():
                        buffer += char