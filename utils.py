#Utils for RFIDMusicBox
import os
import json
import re
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

def get_connected_ssid():
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            active, ssid = line.split(":", 1)
            if active == "yes":
                return ssid
    except Exception as e:
        append_log(f"❌ Feil ved henting av tilkoblet SSID: {e}")
    return None

def get_wifi_ip_address(interface="wlan0"):
    # Brukes i stedet for socket.gethostbyname(socket.gethostname()), som på
    # Linux fort kan returnere 127.0.1.1 (fra /etc/hosts) i stedet for den
    # ekte IP-en på wlan0 - både i vanlig WiFi-modus og i hotspot-modus
    # (der NetworkManager selv setter wlan0 til 10.42.0.1).
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "IP4.ADDRESS", "device", "show", interface],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if line.startswith("IP4.ADDRESS"):
                _, _, value = line.partition(":")
                return value.split("/")[0].strip() or None
    except Exception as e:
        append_log(f"❌ Feil ved henting av IP-adresse: {e}")
    return None

def get_current_volume(default=80):
    try:
        result = subprocess.run(["amixer", "get", "Master"], capture_output=True, text=True)
        match = re.search(r"\[(\d+)%\]", result.stdout)
        if match:
            return int(match.group(1))
    except Exception as e:
        append_log(f"❌ Klarte ikke hente volum: {e}")
    return default

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

def clear_log(log_file="/home/magic/programmer/RFIDMusicBox/activity_log.json"):
    try:
        with open(log_file, "w") as f:
            json.dump([], f, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"❌ Feil ved tømming av logg: {e}")

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
_NOW_PLAYING_FILE = "/tmp/.rfidmusicbox_now_playing.txt"

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

                with open(_NOW_PLAYING_FILE, "w") as f:
                    f.write(label)

                append_log(f"▶ mpv startet via ALSA: {label}")
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
    except Exception as e:
        append_log(f"❌ Feil ved avspilling: {e}")

def get_now_playing():
    # Tittelen på det som faktisk spilles nå, eller None hvis mpv ikke kjører
    # (f.eks. etter Stopp, eller en spilleliste som er ferdig avspilt).
    result = subprocess.run(["pgrep", "-f", "mpv"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        return None
    if os.path.exists(_NOW_PLAYING_FILE):
        with open(_NOW_PLAYING_FILE, "r") as f:
            label = f.read().strip()
            return label or None
    return None

_PARENTAL_LOCK_KEY = "parental_lock_until"

def get_parental_lock_remaining():
    """Sekunder igjen av foreldrelåsen, eller 0 hvis den ikke er aktiv."""
    songs = load_songs()
    until = songs.get(_PARENTAL_LOCK_KEY)
    if not until:
        return 0
    return max(0, until - time.time())

def is_parental_locked():
    return get_parental_lock_remaining() > 0

def set_parental_lock(hours):
    songs = load_songs()
    if hours and hours > 0:
        songs[_PARENTAL_LOCK_KEY] = time.time() + hours * 3600
        save_songs(songs)
        append_log(f"🔒 Foreldrekontroll: spilleren låst i {hours:g} time(r)")
        # Stopp det som evt. allerede spiller - en ny lås skal virke med det samme.
        subprocess.call(["pkill", "-f", "mpv"])
    elif songs.get(_PARENTAL_LOCK_KEY):
        del songs[_PARENTAL_LOCK_KEY]
        save_songs(songs)
        append_log("🔓 Foreldrekontroll: spilleren låst opp")

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

def is_playlist_playing():
    # Brukes av panelet til å bare vise Forrige/Neste-knappene når de faktisk
    # gjør noe - spør den kjørende mpv-prosessen selv (via IPC) om den har mer
    # enn ett spor i sin interne spilleliste, i stedet for å anta ut fra hva
    # som sist ble trigget (som fort kan komme ut av sync).
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            sock.connect(_MPV_IPC_SOCKET)
            sock.sendall((json.dumps({"command": ["get_property", "playlist-count"], "request_id": 1}) + "\n").encode())
            response = sock.recv(4096).decode()
        for line in response.splitlines():
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("request_id") == 1:
                return msg.get("data", 0) > 1
        return False
    except Exception:
        return False

def play_song(filepath, title=None):
    append_log(f"Starter å spille: {filepath}")

    if not os.path.exists(filepath):
        append_log(f"❌ Fil ikke funnet: {filepath}")
        return

    _start_mpv([filepath], title or filepath)

WEBPANEL_PORT = 5000
_TILKOBLINGSINFO_VOLUME = 80
_TILKOBLINGSINFO_WAV = "/tmp/.rfidmusicbox_tilkoblingsinfo.wav"
# Engelsk i stedet for norsk - espeak-ng sin engelske stemme uttaler tall og
# IP-adresser mer forståelig enn den norske. Må virke offline (AP-modus har
# ikke internett), så et offline-motor som espeak-ng er et krav, ikke bare et valg.
_TTS_VOICE = "en-us+f3"  # "+f3" = kvinnelig variant av espeak-ng sin engelske stemme
_TTS_SPEED = 115  # ord/min - saktere enn standard (175) for at tallene skal være til å forstå

def _synthesize_speech(text, output_path, voice=_TTS_VOICE, speed=_TTS_SPEED):
    try:
        subprocess.run(
            ["espeak-ng", "-v", voice, "-s", str(speed), "-w", output_path, text],
            check=True, capture_output=True, timeout=30
        )
        return True
    except Exception as e:
        append_log(f"❌ Klarte ikke generere tale: {e}")
        return False

_DIGIT_WORDS = {"0": "zero", "1": "one", "2": "two", "3": "three", "4": "four",
                "5": "five", "6": "six", "7": "seven", "8": "eight", "9": "nine"}

def _spell_out_digits(digits):
    # Tallordet "hundre og nittito" for "192" er lett å høre feil av - hvert
    # siffer lest for seg (som et telefonnummer) er langt vanskeligere å bomme på.
    return " ".join(_DIGIT_WORDS.get(ch, ch) for ch in digits)

def _spell_out_ip_address(ip):
    # Komma før og etter "dot" gir espeak-ng en liten pause der, slik at
    # skillet mellom oktettene blir tydelig i stedet for å flyte sammen.
    return ", dot, ".join(_spell_out_digits(octet) for octet in ip.split("."))

def build_tilkoblingsinfo_text():
    # Importeres her (ikke øverst i filen) for å unngå en importsløyfe -
    # wifi_watchdog.py importerer selv fra utils.py.
    from wifi_watchdog import is_hotspot_active, HOTSPOT_SSID

    hostname = socket.gethostname()
    friendly_name = f"{hostname}.local"
    ip_address = get_wifi_ip_address()
    ip_spoken = _spell_out_ip_address(ip_address) if ip_address else "an unknown address"
    port_spoken = _spell_out_digits(str(WEBPANEL_PORT))
    wifi_name = HOTSPOT_SSID if is_hotspot_active() else (get_connected_ssid() or "the box's network")

    return (
        f"To connect, join WiFi network {wifi_name}. Open your browser and go to address {friendly_name}, "
        f"or please enter the ip address {ip_spoken}, colon, {port_spoken}."
    )

def speak_tilkoblingsinfo():
    text = build_tilkoblingsinfo_text()
    append_log(f"🗣 Leser opp tilkoblingsinfo: {text}")

    if not _synthesize_speech(text, _TILKOBLINGSINFO_WAV):
        return

    subprocess.run(["amixer", "sset", "Master", f"{_TILKOBLINGSINFO_VOLUME}%"])
    play_song(_TILKOBLINGSINFO_WAV, title="Tilkoblingsinfo")

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

def play_playlist(folder, title=None):
    if not os.path.exists(folder):
        append_log(f"❌ Spilleliste-mappe ikke funnet: {folder}")
        return
    mp3_files = sorted([f for f in os.listdir(folder) if f.endswith(".mp3")])
    if not mp3_files:
        append_log(f"❌ Ingen mp3-filer funnet i spilleliste: {folder}")
        return
    filepaths = [os.path.join(folder, f) for f in mp3_files]
    label = title or f"spilleliste ({len(mp3_files)} filer): {folder}"
    append_log(f"▶ Starter spilleliste med {len(mp3_files)} filer: {folder}")
    _start_mpv(filepaths, label)