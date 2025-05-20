import os
import json
import subprocess
from datetime import datetime

BLUETOOTH_SINK = "bluez_sink.B2_F9_2D_EE_95_9D.a2dp_sink"

def append_log(entry, log_file="/home/magic/RFIDMusicBox/activity_log.json", max_lines=100):
    try:
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                try:
                    log = json.load(f)
                except json.JSONDecodeError:
                    log = []
        else:
            log = []

        timestamp = datetime.now().strftime("%H:%M:%S")
        log.insert(0, {"time": timestamp, "entry": entry})

        with open(log_file, "w") as f:
            json.dump(log[:max_lines], f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"❌ Feil ved logging: {e}")

def load_log(log_file="/home/magic/RFIDMusicBox/activity_log.json"):
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def load_songs(song_file="/home/magic/RFIDMusicBox/songs.json"):
    if os.path.exists(song_file):
        with open(song_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_songs(songs, song_file="/home/magic/RFIDMusicBox/songs.json"):
    try:
        with open(song_file, "w") as f:
            json.dump(songs, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"❌ Feil ved lagring av sanger: {e}")

def play_song(filepath):
    if not os.path.exists(filepath):
        append_log(f"❌ Fil ikke funnet: {filepath}")
        return

    # Stopp tidligere mpv-prosesser
    subprocess.call(["pkill", "-f", "mpv"])

    try:
        result = subprocess.run(
            ["pactl", "get-sink-state", BLUETOOTH_SINK],
            capture_output=True, text=True
        )

        if result.returncode == 0 and any(state in result.stdout for state in ["RUNNING", "IDLE", "SUSPENDED"]):
            append_log("🔊 Spiller via Bluetooth")
            subprocess.Popen([
                "env", f"PULSE_SINK={BLUETOOTH_SINK}",
                "mpv", "--no-video", "--force-window=no", filepath
            ])
        else:
            append_log("🔈 Spiller via systemets standardutgang")
            subprocess.Popen([
                "mpv", "--no-video", "--force-window=no", filepath
            ])

    except Exception as e:
        append_log(f"❌ Feil ved avspilling: {e}")