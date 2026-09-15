from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
import shutil
import subprocess
import socket
from datetime import datetime
from utils import (
    append_log,
    load_log,
    load_songs,
    save_songs,
    play_song,
    is_youtube_playlist,
    download_youtube_playlist,
    play_playlist,
    find_song_by_rfid,
    skip_to_next_track,
    skip_to_previous_track,
    is_playlist_playing,
    get_now_playing,
    list_audio_devices_with_friendly_names as list_audio_devices,
    get_current_default_sink,  # ← riktig funksjon her
    get_current_volume
)

#13:11
app = Flask(__name__)

STORAGE_DIR = "/home/magic/programmer/RFIDMusicBox/mp3"
SONGS_FILE = "/home/magic/programmer/RFIDMusicBox/songs.json"
REPO_DIR = "/home/magic/programmer/RFIDMusicBox"

def get_git_version():
    try:
        commit = subprocess.run(
            ["git", "-C", REPO_DIR, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        date = subprocess.run(
            ["git", "-C", REPO_DIR, "log", "-1", "--format=%cd", "--date=short"],
            capture_output=True, text=True, timeout=5
        )
        return {
            "commit": commit.stdout.strip() if commit.returncode == 0 else "ukjent",
            "date": date.stdout.strip() if date.returncode == 0 else "",
        }
    except Exception:
        return {"commit": "ukjent", "date": ""}

def get_git_log(limit=50):
    try:
        result = subprocess.run(
            ["git", "-C", REPO_DIR, "log", f"-{limit}", "--date=short",
             "--pretty=format:%h\x1f%ad\x1f%an\x1f%s"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return []
        commits = []
        for line in result.stdout.splitlines():
            parts = line.split("\x1f")
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0], "date": parts[1], "author": parts[2], "message": parts[3]
                })
        return commits
    except Exception:
        return []

@app.route("/changelog")
def changelog():
    return render_template("changelog.html", commits=get_git_log(), version=get_git_version())

@app.route("/edit_title", methods=["POST"])
def edit_title():
    song_id = request.form.get("song_id")
    new_title = request.form.get("new_title", "").strip()

    songs = load_songs()
    if song_id in songs and new_title:
        songs[song_id]["title"] = new_title
        save_songs(songs)
        append_log(f"✏️ Endret tittel på {song_id} til: {new_title}")
    else:
        append_log(f"❌ Kunne ikke endre tittel (ID: {song_id})")

    return redirect("/")

@app.route("/")
def index():
    songs = load_songs()
    ip = request.host
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    log = load_log()
    audio_devices = list_audio_devices()
    current_sink = get_current_default_sink()
    current_volume = get_current_volume()
    connected_ssid = get_connected_ssid()

    # 🔍 Slå opp friendly name
    current_sink_friendly = None
    for device in audio_devices:
        if device.get("name") == current_sink:
            current_sink_friendly = device.get("friendly")
            break

    return render_template("index.html",
        songs=songs,
        ip=ip,
        ip_address=ip_address,
        log=log,
        audio_devices=audio_devices,
        current_sink=current_sink,
        current_sink_friendly=current_sink_friendly,
        current_volume=current_volume,
        connected_ssid=connected_ssid,
        playlist_playing=is_playlist_playing(),
        now_playing=get_now_playing(),
        version=get_git_version()
    )

@app.route("/set_default_device", methods=["POST"])
def set_default_device():
    sink_name = request.form.get("device_name")
    try:
        subprocess.run(["pkill", "-f", "mpv"])  # 🔇 Stopp aktiv avspilling før bytte
        subprocess.run(["pactl", "set-default-sink", sink_name], check=True)
        append_log(f"🔊 Standard lydenhet satt til: {sink_name}")
    except Exception as e:
        append_log(f"❌ Feil ved setting av lydenhet: {e}")
    return redirect("/")



def is_valid_url(url):
    return url.startswith("http") and (
        "youtube.com" in url or "youtu.be" in url
    )

@app.route("/status")
def status():
    data = load_songs()
    rfid = data.get("last_read_rfid", "")
    match = find_song_by_rfid(data, rfid)
    valid = False
    if match:
        if match.get("type") == "song" and "filename" in match:
            valid = os.path.exists(os.path.join(STORAGE_DIR, match["filename"]))
        elif match.get("type") == "playlist" and "playlist_dir" in match:
            folder_path = os.path.join(STORAGE_DIR, match["playlist_dir"])
            valid = os.path.exists(folder_path) and any(f.endswith(".mp3") for f in os.listdir(folder_path))
    return jsonify({
        "rfid": rfid,
        "status": "ready" if valid else "missing",
        "playlist_playing": is_playlist_playing(),
        "now_playing": get_now_playing()
    })

@app.route("/log")
def log():
    return jsonify(load_log())

@app.route("/help")
def help_page():
    return render_template("help.html")

UPDATE_SCRIPT = "/home/magic/programmer/RFIDMusicBox/scripts/git_update.sh"

def run_full_update():
    try:
        result = subprocess.run(
            ["bash", UPDATE_SCRIPT, "--full"], capture_output=True, text=True, timeout=600
        )
        output = result.stdout.strip()
        for line in output.splitlines():
            if line and line != "UPDATED":
                append_log(line)

        if "UPDATED" in output.splitlines():
            append_log("🔁 Oppdatering hentet - starter Pi-en på nytt om noen sekunder for å ta den i bruk")
            # Kort forsinkelse slik at denne HTTP-forespørselen rekker å bli
            # besvart før webpanel-prosessen selv blir tatt ned av omstarten.
            subprocess.Popen(["bash", "-c", "sleep 3 && sudo systemctl reboot"])
        else:
            append_log("✅ Sjekket etter oppdatering - alt er allerede oppdatert")
    except Exception as e:
        append_log(f"❌ Feil ved sjekk etter oppdatering: {e}")

@app.route("/update", methods=["POST"])
def update_from_git():
    # Kjøres i bakgrunnen: en full oppdatering (kode + Python-avhengigheter +
    # systempakker via apt) kan ta flere minutter, og skal ikke la denne
    # HTTP-forespørselen henge og vente.
    append_log("🔄 Starter full oppdatering (kode, avhengigheter, systempakker) - dette kan ta noen minutter...")
    subprocess.Popen(["python3", __file__, "--full-update"])
    return redirect("/")

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

def scan_wifi_networks():
    networks = []
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL", "dev", "wifi"],
            capture_output=True, text=True, timeout=10
        )
        seen = set()
        for line in result.stdout.splitlines():
            parts = line.split(":")
            if len(parts) < 2:
                continue
            ssid, signal = parts[0], parts[1]
            if ssid and ssid not in seen:
                seen.add(ssid)
                networks.append({"ssid": ssid, "signal": signal})
    except Exception as e:
        append_log(f"❌ Feil ved skanning av WiFi-nettverk: {e}")
    return networks

@app.route("/wifi")
def wifi_settings():
    connected_ssid = get_connected_ssid()
    networks = scan_wifi_networks()
    return render_template("wifi.html", connected=connected_ssid, networks=networks)

@app.route("/connect_wifi", methods=["POST"])
def connect_wifi():
    ssid = request.form.get("ssid", "").strip()
    password = request.form.get("password", "")
    if not ssid:
        append_log("❌ Ingen SSID oppgitt for WiFi-tilkobling")
        return redirect("/wifi")
    try:
        subprocess.run(
            ["nmcli", "dev", "wifi", "connect", ssid, "password", password],
            check=True, timeout=30
        )
        append_log(f"📶 Koblet til WiFi: {ssid}")
    except Exception as e:
        append_log(f"❌ Klarte ikke koble til {ssid}: {e}")
    return redirect("/wifi")

@app.route("/disconnect_wifi", methods=["POST"])
def disconnect_wifi():
    try:
        # "device disconnect" tar ned hva enn som er aktivt på wlan0, uavhengig
        # av hva selve tilkoblingsprofilen heter (varierer med hvordan den ble
        # opprettet - f.eks. "netplan-wlan0-<ssid>" fra cloud-init, eller bare
        # <ssid> fra nmcli/denne siden - "connection down wlan0" antok feilaktig
        # at profilen alltid het nøyaktig "wlan0").
        subprocess.run(["nmcli", "device", "disconnect", "wlan0"], check=True, timeout=10)
        append_log("📶 Koblet fra WiFi")
    except Exception as e:
        append_log(f"❌ Klarte ikke koble fra: {e}")
    return redirect("/wifi")

def _parse_bluetoothctl_devices(output):
    devices = []
    for line in output.splitlines():
        if line.startswith("Device"):
            parts = line.split(" ", 2)
            if len(parts) == 3:
                devices.append({"addr": parts[1], "name": parts[2]})
    return devices

def get_paired_bluetooth_devices():
    try:
        result = subprocess.run(
            ["bluetoothctl", "paired-devices"], capture_output=True, text=True, timeout=10
        )
        return _parse_bluetoothctl_devices(result.stdout)
    except Exception as e:
        append_log(f"❌ Feil ved henting av parede Bluetooth-enheter: {e}")
        return []

def get_connected_bluetooth_addrs():
    try:
        result = subprocess.run(
            ["bluetoothctl", "devices", "Connected"], capture_output=True, text=True, timeout=10
        )
        return {d["addr"] for d in _parse_bluetoothctl_devices(result.stdout)}
    except Exception:
        return set()

def get_all_known_bluetooth_devices():
    try:
        result = subprocess.run(
            ["bluetoothctl", "devices"], capture_output=True, text=True, timeout=10
        )
        return _parse_bluetoothctl_devices(result.stdout)
    except Exception as e:
        append_log(f"❌ Feil ved henting av Bluetooth-enheter: {e}")
        return []

def find_pulse_sink_for_bluetooth(addr):
    # PulseAudio/PipeWire navngir Bluetooth-sinker etter MAC-adressen med
    # kolon byttet ut med understrek, f.eks. bluez_sink.AA_BB_CC_DD_EE_FF.a2dp_sink
    mac_pattern = addr.replace(":", "_")
    for device in list_audio_devices():
        if mac_pattern in device.get("name", ""):
            return device["name"]
    return None

@app.route("/bluetooth")
def bluetooth_settings():
    paired = get_paired_bluetooth_devices()
    paired_addrs = {d["addr"] for d in paired}
    connected_addrs = get_connected_bluetooth_addrs()
    for d in paired:
        d["connected"] = d["addr"] in connected_addrs
        d["sink"] = find_pulse_sink_for_bluetooth(d["addr"]) if d["connected"] else None

    discovered = [
        d for d in get_all_known_bluetooth_devices() if d["addr"] not in paired_addrs
    ]

    return render_template("bluetooth.html", paired=paired, discovered=discovered)

@app.route("/bluetooth/scan", methods=["POST"])
def bluetooth_scan():
    append_log("🔍 Søker etter Bluetooth-enheter (ca. 8 sekunder)...")
    try:
        subprocess.run(
            ["bluetoothctl", "--timeout", "8", "scan", "on"],
            capture_output=True, text=True, timeout=15
        )
        append_log("✅ Bluetooth-søk fullført")
    except Exception as e:
        append_log(f"❌ Feil ved søk etter Bluetooth-enheter: {e}")
    return redirect("/bluetooth")

@app.route("/bluetooth/pair", methods=["POST"])
def bluetooth_pair():
    addr = request.form.get("addr", "").strip()
    if not addr:
        append_log("❌ Ingen Bluetooth-adresse oppgitt for paring")
        return redirect("/bluetooth")
    try:
        subprocess.run(["bluetoothctl", "pair", addr], check=True, timeout=20)
        subprocess.run(["bluetoothctl", "trust", addr], check=True, timeout=10)
        subprocess.run(["bluetoothctl", "connect", addr], check=True, timeout=15)
        append_log(f"🔵 Paret og koblet til Bluetooth-enhet: {addr}")
    except Exception as e:
        append_log(f"❌ Klarte ikke pare Bluetooth-enhet {addr}: {e}")
    return redirect("/bluetooth")

@app.route("/bluetooth/connect", methods=["POST"])
def bluetooth_connect():
    addr = request.form.get("addr", "").strip()
    if not addr:
        return redirect("/bluetooth")
    try:
        subprocess.run(["bluetoothctl", "connect", addr], check=True, timeout=15)
        append_log(f"🔵 Koblet til Bluetooth-enhet: {addr}")
    except Exception as e:
        append_log(f"❌ Klarte ikke koble til Bluetooth-enhet {addr}: {e}")
    return redirect("/bluetooth")

@app.route("/bluetooth/remove", methods=["POST"])
def bluetooth_remove():
    addr = request.form.get("addr", "").strip()
    if not addr:
        return redirect("/bluetooth")
    try:
        subprocess.run(["bluetoothctl", "remove", addr], check=True, timeout=10)
        append_log(f"🗑 Fjernet Bluetooth-enhet: {addr}")
    except Exception as e:
        append_log(f"❌ Klarte ikke fjerne Bluetooth-enhet {addr}: {e}")
    return redirect("/bluetooth")

def download_song(song_id, url):
    if is_youtube_playlist(url):
        playlist_dir = f"playlist_{song_id}"
        full_path = os.path.join(STORAGE_DIR, playlist_dir)
        os.makedirs(full_path, exist_ok=True)
        success = download_youtube_playlist(url, full_path)

        # Last inn på nytt etter (potensielt lang) nedlasting - sangen kan ha
        # blitt slettet fra panelet i mellomtiden. Ikke la filene bli liggende
        # foreldreløse på disk hvis oppføringen er borte.
        songs = load_songs()
        if song_id not in songs:
            shutil.rmtree(full_path, ignore_errors=True)
            append_log(f"⚠️ Spilleliste slettet før nedlasting fullførte - fjernet {playlist_dir} igjen")
            return

        if success:
            songs[song_id]["status"] = "ready"
            songs[song_id]["playlist_dir"] = playlist_dir
            meta = subprocess.run(
                ["yt-dlp", "--flat-playlist", "--playlist-items", "1", "--print", "%(playlist_title)s", url],
                capture_output=True, text=True
            )
            songs[song_id]["title"] = meta.stdout.strip() if meta.returncode == 0 and meta.stdout.strip() else playlist_dir
            append_log(f"📥 Lastet ned spilleliste: {songs[song_id]['title']}")
        else:
            songs[song_id]["status"] = "error"
            append_log(f"❌ Feil ved nedlasting av spilleliste: {url}")
    else:
        filename = f"song_{song_id}.mp3"
        full_path = os.path.join(STORAGE_DIR, filename)
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", url, "-o", full_path]
        result = subprocess.run(cmd)

        songs = load_songs()
        if song_id not in songs:
            if os.path.exists(full_path):
                os.remove(full_path)
            append_log(f"⚠️ Sang slettet før nedlasting fullførte - fjernet {filename} igjen")
            return

        if result.returncode == 0:
            songs[song_id]["status"] = "ready"
            songs[song_id]["filename"] = filename
            meta = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True)
            songs[song_id]["title"] = meta.stdout.strip() if meta.returncode == 0 else filename
            append_log(f"🎵 Lastet ned sang: {songs[song_id]['title']}")
        else:
            songs[song_id]["status"] = "error"
            append_log(f"❌ Nedlasting feilet: {url}")
    save_songs(songs)

@app.route("/add_url", methods=["POST"])
def add_url():
    url = request.form["url"].strip()
    if not is_valid_url(url):
        append_log("❌ Ugyldig URL lagt inn")
        return redirect("/")

    song_id = str(int(datetime.now().timestamp() * 1000))
    songs = load_songs()
    song_type = "playlist" if is_youtube_playlist(url) else "song"
    songs[song_id] = {"url": url, "status": "downloading", "type": song_type}
    save_songs(songs)

    append_log(f"🆕 Nå er en ny {'liste' if song_type == 'playlist' else 'sang'} registrert: {url}")
    subprocess.Popen(["python3", __file__, "--download", song_id])
    return redirect("/")

@app.route("/play", methods=["POST"])
def play_song_route():
    song_id = request.form["song_id"]
    songs = load_songs()

    if song_id not in songs:
        append_log(f"❌ Ugyldig song_id: {song_id}")
        return redirect("/")

    song = songs[song_id]

    if song.get("type") == "playlist" and "playlist_dir" in song:
        folder = os.path.join(STORAGE_DIR, song["playlist_dir"])
        play_playlist(folder, title=song.get("title"))
    elif song.get("type") == "song" and "filename" in song:
        filepath = os.path.join(STORAGE_DIR, song["filename"])
        play_song(filepath, title=song.get("title"))
    else:
        append_log("⚠️ Ukjent sangtype eller mangler fil/dir")

    return redirect("/")

@app.route("/delete_song", methods=["POST"])
def delete_song():
    song_id = request.form["song_id"]
    songs = load_songs()
    song = songs.get(song_id)

    # Slett MP3-fil eller spillelistemappe hvis den finnes
    if song and "filename" in song:
        filepath = os.path.join(STORAGE_DIR, song["filename"])
        if os.path.exists(filepath):
            os.remove(filepath)
    elif song and "playlist_dir" in song:
        dirpath = os.path.join(STORAGE_DIR, song["playlist_dir"])
        if os.path.exists(dirpath):
            shutil.rmtree(dirpath)

    # Slett sang fra listen
    if song_id in songs:
        append_log(f"🗑 Slettet sang: {songs[song_id].get('title', song_id)}")
        del songs[song_id]
        save_songs(songs)

    return redirect("/")

@app.route("/stop", methods=["POST"])
def stop_song():
    subprocess.run(["pkill", "-f", "mpv"])
    append_log("⏹ Stoppet avspilling")
    return redirect("/")

@app.route("/skip_next", methods=["POST"])
def skip_next():
    skip_to_next_track()
    return redirect("/")

@app.route("/skip_previous", methods=["POST"])
def skip_previous():
    skip_to_previous_track()
    return redirect("/")

@app.route("/set_volume", methods=["POST"])
def set_volume():
    try:
        volume = int(request.form.get("volume", 0))
        if 0 <= volume <= 150:
            subprocess.run(["amixer", "sset", "Master", f"{volume}%"], check=True)
            append_log(f"🔊 Volum satt til {volume}%")
            return redirect(url_for("index"))
        else:
            append_log(f"⚠️ Ugyldig volumverdi: {volume}")
            return "Ugyldig volumverdi", 400
    except Exception as e:
        append_log(f"❌ Feil ved setting av volum: {e}")
        return f"Feil: {e}", 500

@app.route("/link_rfid", methods=["POST"])
def link_rfid():
    song_id = request.form["song_id"]
    songs = load_songs()
    rfid = songs.get("last_read_rfid")

    if not rfid:
        append_log("⚠️ Ingen RFID skannet ennå.")
        return redirect("/")

    if song_id not in songs:
        append_log(f"❌ Ugyldig song_id: {song_id}")
        return redirect("/")

    songs[song_id]["rfid"] = rfid
    append_log(f"🔗 Knyttet RFID {rfid} til sang: {songs[song_id].get('title', 'Ukjent')}")
    save_songs(songs)
    return redirect("/")

@app.route("/unlink_rfid", methods=["POST"])
def unlink_rfid():
    song_id = request.form["song_id"]
    songs = load_songs()
    if "rfid" in songs.get(song_id, {}):
        del songs[song_id]["rfid"]
        append_log(f"🚫 Fjernet RFID fra {songs[song_id].get('title', song_id)}")
        save_songs(songs)
    return redirect("/")

def resume_stuck_downloads():
    # Blir en nedlasting avbrutt (f.eks. Pi-en restartet midt i via "Oppdater
    # app"), blir oppføringen stående på status "downloading" for alltid - ingen
    # automatikk plukket den opp igjen. Gjenopptar dem her, ved hver oppstart av
    # webpanelet: yt-dlp hopper selv over filer som allerede er lastet ned, så
    # dette fortsetter kun med det som mangler i stedet for å starte på nytt.
    songs = load_songs()
    stuck = [sid for sid, song in songs.items() if isinstance(song, dict) and song.get("status") == "downloading"]
    for sid in stuck:
        append_log(f"🔁 Gjenopptar avbrutt nedlasting: {songs[sid].get('title', sid)}")
        subprocess.Popen(["python3", __file__, "--download", sid])

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--download":
        sid = sys.argv[2]
        songs = load_songs()
        if sid in songs:
            download_song(sid, songs[sid]["url"])
    elif len(sys.argv) == 2 and sys.argv[1] == "--full-update":
        run_full_update()
    else:
        append_log("🌍 Starter webpanel på port 5000")
        resume_stuck_downloads()
        app.run(host="0.0.0.0", port=5000)