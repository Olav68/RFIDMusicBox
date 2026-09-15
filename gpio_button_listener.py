# gpio_button_listener.py - Leser fysiske knapper (volum opp/ned, stopp,
# spill av igjen) koblet til GPIO-pinnene på Pi-en.
import os
import subprocess
from gpiozero import Button
from signal import pause
from utils import append_log, load_songs, play_song, play_playlist, find_song_by_rfid

STORAGE_DIR = "/home/magic/programmer/RFIDMusicBox/mp3"

# BCM-pinnenummer - endre her hvis knappene kobles til andre GPIO-pinner.
# Hver knapp kobles mellom pinnen og GND; gpiozero bruker Pi-ens interne
# pull-up som standard, så ingen eksterne motstander er nødvendig.
VOLUME_UP_PIN = 6
VOLUME_DOWN_PIN = 5
STOP_PIN = 13
REPLAY_PIN = 19

VOLUME_STEP = "5%"


def volume_up():
    subprocess.run(["amixer", "sset", "Master", f"{VOLUME_STEP}+"])
    append_log("🔊 Volum opp (knapp)")


def volume_down():
    subprocess.run(["amixer", "sset", "Master", f"{VOLUME_STEP}-"])
    append_log("🔉 Volum ned (knapp)")


def stop():
    subprocess.run(["pkill", "-f", "mpv"])
    append_log("⏹ Stoppet avspilling (knapp)")


def replay():
    songs = load_songs()
    rfid = songs.get("last_read_rfid", "")
    song = find_song_by_rfid(songs, rfid) if rfid else None

    if not song:
        append_log("⚠️ Ingen sang å spille av igjen (knapp)")
        return

    if song.get("type") == "playlist" and "playlist_dir" in song:
        folder = os.path.join(STORAGE_DIR, song["playlist_dir"])
        append_log(f"🔁 Spiller av igjen (knapp): {song.get('title', folder)}")
        play_playlist(folder)
    elif "filename" in song:
        filepath = os.path.join(STORAGE_DIR, song["filename"])
        append_log(f"🔁 Spiller av igjen (knapp): {song.get('title', filepath)}")
        play_song(filepath)
    else:
        append_log("⚠️ Ingen gyldig kilde for sist spilte sang (knapp)")


def main():
    append_log("🔌 Starter GPIO-knappelytter")

    volume_up_button = Button(VOLUME_UP_PIN)
    volume_down_button = Button(VOLUME_DOWN_PIN)
    stop_button = Button(STOP_PIN)
    replay_button = Button(REPLAY_PIN)

    volume_up_button.when_pressed = volume_up
    volume_down_button.when_pressed = volume_down
    stop_button.when_pressed = stop
    replay_button.when_pressed = replay

    pause()


if __name__ == "__main__":
    main()
