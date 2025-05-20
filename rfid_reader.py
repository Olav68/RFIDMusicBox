#!/usr/bin/env python3
import os
import json
import time
import pygame
import RPi.GPIO as GPIO
from utils import append_log

SONGS_FILE = "/home/magic/RFIDMusicBox/songs.json"
MP3_DIR = "/home/magic/RFIDMusicBox/mp3"
LOG_FILE = "/home/magic/RFIDMusicBox/activity_log.json"
RFID_DEVICE = "/dev/ttyUSB0"

def load_songs():
    try:
        with open(SONGS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        append_log(f"❌ Klarte ikke å laste sanger: {e}")
        return {}

def play_mp3(filename):
    path = os.path.join(MP3_DIR, filename)
    if os.path.exists(path):
        append_log(f"▶️ Spiller: {filename}")
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
    else:
        append_log(f"⚠️ MP3 ikke funnet: {filename}")

def read_rfid():
    try:
        with open(RFID_DEVICE, "r") as device:
            while True:
                rfid = device.readline().strip()
                if rfid:
                    append_log(f"📡 RFID skannet: {rfid}")
                    yield rfid
    except Exception as e:
        append_log(f"❌ Feil ved lesing av RFID: {e}")
        time.sleep(2)

def main():
    append_log("📻 RFID-leser startet")
    songs = load_songs()
    played = set()

    for rfid in read_rfid():
        if rfid in songs:
            if rfid not in played:
                played.add(rfid)
                play_mp3(songs[rfid]["filename"])
        else:
            append_log(f"🔎 Ingen sang funnet for RFID: {rfid}")

if __name__ == "__main__":
    main()