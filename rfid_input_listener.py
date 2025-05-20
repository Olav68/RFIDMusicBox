import os
import json
from evdev import InputDevice, categorize, ecodes, list_devices
from utils import append_log, load_songs, save_songs

SONGS_FILE = "/home/magic/RFIDMusicBox/songs.json"
DEVICE_NAME = "RFIDeas USB Keyboard"


def find_device():
    print("🔍 Søker etter RFID-leser...")
    for path in list_devices():
        device = InputDevice(path)
        if DEVICE_NAME in device.name:
            print(f"✅ Fant {device.name} @ {path}")
            return device
    print("❌ Ingen RFID-leser funnet")
    return None


def main():
    append_log("🔌 Starter RFID input listener")
    device = find_device()
    if not device:
        append_log("❌ Fant ikke RFID-enhet")
        return

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

                    append_log(f"📥 RFID registrert: {rfid}")
                    songs = load_songs()
                    songs["last_read_rfid"] = rfid
                    save_songs(songs)
                else:
                    if len(char) == 1:
                        buffer += char


if __name__ == "__main__":
    main()