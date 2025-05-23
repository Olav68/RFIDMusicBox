#Utils for RFIDMusicBox
import os
import json
import re
import subprocess
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def list_audio_devices():
    try:
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
        output = result.stdout

        devices = []
        for line in output.splitlines():
            match = re.match(r"card (\d+): (\S+) \[(.+?)\], device (\d+): (.+?) \[(.+?)\]", line)
            if match:
                card = match.group(1)
                description = match.group(3)
                devices.append({
                    "card": card,
                    "name": description
                })
        return devices
    except Exception as e:
        append_log(f"❌ Klarte ikke hente lydenheter: {e}")
        return []

def update_default_audio_device(card_number):
    try:
        asoundrc_path = os.path.expanduser("~/.asoundrc")
        content = f"""
defaults.pcm.card {card_number}
defaults.ctl.card {card_number}
"""
        with open(asoundrc_path, "w") as f:
            f.write(content.strip())
        append_log(f"🎚 Oppdaterte standard lydenhet til kort {card_number}")
    except Exception as e:
        append_log(f"❌ Klarte ikke oppdatere .asoundrc: {e}")

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
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        return "list" in query and query["list"][0].startswith("PL")
    except Exception:
        return False

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

def play_playlist(folder):
    if not os.path.exists(folder):
        append_log(f"❌ Spilleliste-mappe ikke funnet: {folder}")
        return
    mp3_files = sorted([f for f in os.listdir(folder) if f.endswith(".mp3")])
    append_log(f"▶ Starter spilleliste med {len(mp3_files)} filer: {folder}")
    for mp3 in mp3_files:
        filepath = os.path.join(folder, mp3)
        append_log(f"▶ Spiller fra liste: {mp3}")
        play_song(filepath)