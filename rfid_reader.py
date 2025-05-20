import serial
import os
import subprocess
import json
from utils import append_log, load_songs, save_songs

STORAGE_DIR = "/home/magic/RFIDMusicBox/mp3"
PORT = "/dev/ttyUSB0"  # Eller ttyACM0, juster hvis nødvendig

ser = serial.Serial(PORT, 9600)

while True:
    rfid = ser.readline().decode().strip()
    if not rfid:
        continue

    append_log(f"📡 RFID skannet: {rfid}")

    songs = load_songs()
    songs["last_read_rfid"] = rfid  # For webpanelet

    for sid, info in songs.items():
        if sid == "last_read_rfid":
            continue
        if isinstance(info, dict) and info.get("rfid") == rfid:
            filepath = os.path.join(STORAGE_DIR, info["filename"])
            if os.path.exists(filepath):
                append_log(f"▶ Spiller sang for RFID: {info.get('title', sid)}")
                subprocess.Popen(["mpv", "--no-video", filepath])
            else:
                append_log(f"❌ Fil ikke funnet for {sid}")
            break
    else:
        append_log("⚠️ RFID ikke koblet til noen sang")

    save_songs(songs)