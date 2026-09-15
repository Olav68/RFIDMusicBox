#Utils for RFIDMusicBox
import os
import json
import socket
import subprocess
import time
import fcntl
from datetime import datetime
from urllib.parse import urlparse, parse_qs

def list_audio_devices_with_friendly_names():
    try:
        result = subprocess.run(["pactl", "list", "sinks"], capture_output=True, text=True)
        output = result.stdout

        devices = []
        current = {}
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("Sink #"):
                if current:
                    devices.append(current)
                current = {}
            elif line.startswith("Name:"):
                current["name"] = line.split("Name:")[1].strip()
            elif line.startswith("Description:"):
                current["friendly"] = line.split("Description:")[1].strip()
        if current:
            devices.append(current)
        return devices
    except Exception as e:
        append_log(f"❌ Klarte ikke hente lydutganger: {e}")
        return []

def get_current_default_sink():
    try:
        result = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        append_log(f"❌ Klarte ikke hente aktiv lydenhet: {e}")
        return None

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

_PLAYBACK_LOCK_FILE = "/tmp/.rfidmusicbox_playback.lock"
_MPV_IPC_SOCKET = "/tmp/.rfidmusicbox_mpv.sock"

def _wait_until_mpv_stopped(timeout=2.0, poll_interval=0.05):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = subprocess.run(["pgrep", "-f", "mpv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode != 0:
            return
        time.sleep(poll_interval)

def _start_mpv(filepaths, label):
    try:
        # webpanel.py (flere samtidige forespørsler i egne tråder) og
        # rfid_trigger_listener.py (egen prosess) kan begge kalle denne
        # samtidig. Uten en lås kan to kall begge se "ingen mpv kjører"
        # rett etter at de har drept den forrige, og starte hver sin nye
        # prosess samtidig - sangen spilles da av to ganger på én gang.
        with open(_PLAYBACK_LOCK_FILE, "w") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                subprocess.call(["pkill", "-f", "mpv"])
                _wait_until_mpv_stopped()
                append_log("🔇 Tidligere mpv-prosess stoppet")

                # mpv spiller flere filer i rekkefølge som en spilleliste av seg selv
                # og går videre til neste når én er ferdig - én prosess holder derfor
                # for både enkeltsanger og hele spillelister. IPC-socket-en lar oss
                # senere styre den kjørende prosessen (f.eks. hoppe til neste spor)
                # uten å måtte drepe og starte den på nytt - se skip_to_next_track().
                subprocess.Popen([
                    "mpv", "--ao=alsa", "--no-video", "--force-window=no",
                    f"--input-ipc-server={_MPV_IPC_SOCKET}", *filepaths
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

                append_log(f"▶ mpv startet via ALSA: {label}")
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
    except Exception as e:
        append_log(f"❌ Feil ved avspilling: {e}")

def _send_mpv_command(command):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.settimeout(2)
        sock.connect(_MPV_IPC_SOCKET)
        sock.sendall((json.dumps({"command": command}) + "\n").encode())

def skip_to_next_track():
    try:
        _send_mpv_command(["playlist-next", "weak"])
        append_log("⏭ Hoppet til neste spor")
    except Exception as e:
        append_log(f"❌ Klarte ikke hoppe til neste spor (spilles det av en spilleliste nå?): {e}")

def skip_to_previous_track():
    try:
        _send_mpv_command(["playlist-prev", "weak"])
        append_log("⏮ Hoppet til forrige spor")
    except Exception as e:
        append_log(f"❌ Klarte ikke hoppe til forrige spor (spilles det av en spilleliste nå?): {e}")

def play_song(filepath):
    append_log(f"Starter å spille: {filepath}")

    if not os.path.exists(filepath):
        append_log(f"❌ Fil ikke funnet: {filepath}")
        return

    _start_mpv([filepath], filepath)

def find_song_by_rfid(data, rfid_code):
    for key, val in data.items():
        if isinstance(val, dict) and val.get("rfid") == rfid_code:
            return val
    return None

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
            # Filnavn sortert alfabetisk (det play_playlist() bruker) må matche
            # den ekte spillelisterekkefølgen - uten indeksprefiks havner filene
            # i tilfeldig alfabetisk rekkefølge etter tittel, som er spesielt
            # ødeleggende for lydbøker der kapittelrekkefølgen betyr noe.
            "-o", f"{target_folder}/%(playlist_index)03d - %(title)s.%(ext)s"
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
    if not mp3_files:
        append_log(f"❌ Ingen mp3-filer funnet i spilleliste: {folder}")
        return
    filepaths = [os.path.join(folder, f) for f in mp3_files]
    append_log(f"▶ Starter spilleliste med {len(mp3_files)} filer: {folder}")
    _start_mpv(filepaths, f"spilleliste ({len(mp3_files)} filer): {folder}")