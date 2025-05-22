
import os
import json
import subprocess
from datetime import datetime

def append_log(entry, log_file="/home/magic/programmer/RFIDMusicBox/activity_log.json", max_lines=100):
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

def load_log(log_file="/home/magic/programmer/RFIDMusicBox/activity_log.json"):
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def load_songs(song_file="/home/magic/programmer/RFIDMusicBox/songs.json"):
    if os.path.exists(song_file):
        with open(song_file, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_songs(songs, song_file="/home/magic/programmer/RFIDMusicBox/songs.json"):
    try:
        with open(song_file, "w") as f:
            json.dump(songs, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"❌ Feil ved lagring av sanger: {e}")

def play_song(filepath):
    append_log(f"Starter å spille: {filepath}")

    if not os.path.exists(filepath):
        append_log(f"❌ Fil ikke funnet: {filepath}")
        return

    try:
        subprocess.call(["pkill", "-f", "mpv"])
        append_log("🔇 Tidligere mpv-prosess stoppet")

        subprocess.Popen([
            "mpv", "--ao=alsa", "--no-video", "--force-window=no", filepath
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        append_log(f"▶ mpv startet via ALSA: {filepath}")
    except Exception as e:
        append_log(f"❌ Feil ved avspilling i play_song(): {e}")

def is_youtube_playlist(url):
    return "youtube.com/playlist?list=" in url or "&list=" in url

def download_youtube_playlist(url, target_folder):
    try:
        os.makedirs(target_folder, exist_ok=True)
        cmd = [
            "yt-dlp",
            "-x", "--audio-format", "mp3",
            url,
            "-o", f"{target_folder}/%(title)s.%(ext)s"
        ]
        result = subprocess.run(cmd)
        return result.returncode == 0
    except Exception as e:
        append_log(f"❌ Feil ved nedlasting av spilleliste: {e}")
        return False
