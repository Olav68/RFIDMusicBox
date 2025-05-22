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
                            if "playlist_dir" in song:
                                playlist_path = os.path.join(STORAGE_DIR, song["playlist_dir"])
                                if os.path.isdir(playlist_path):
                                    mp3_files = sorted([
                                        os.path.join(playlist_path, f)
                                        for f in os.listdir(playlist_path)
                                        if f.endswith(".mp3")
                                    ])
                                    append_log(f"▶ Spiller spilleliste: {song.get('title', sid)}")
                                    for file in mp3_files:
                                        play_song(file)
                                else:
                                    append_log(f"❌ Mappen finnes ikke: {playlist_path}")
                            else:
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
