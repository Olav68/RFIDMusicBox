from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
import subprocess
import socket
from datetime import datetime
from bluetooth import bluetooth_bp
from utils import append_log, load_log, load_songs, save_songs, play_song

app = Flask(__name__)
app.register_blueprint(bluetooth_bp)
STORAGE_DIR = "/home/magic/RFIDMusicBox/mp3"
SONGS_FILE = "/home/magic/RFIDMusicBox/songs.json"
MUSIC_DIR = "/home/magic/RFIDMusicBox/music"

def is_valid_url(url):
    return url.startswith("http") and (
        "youtube.com" in url or "spotify.com" in url or "youtu.be" in url
    )

def load_songs():
    if os.path.exists(SONGS_FILE):
        with open(SONGS_FILE, "r") as f:
            return json.load(f)
    return {}

def find_song_by_rfid(data, rfid_code):
    for key, val in data.items():
        if isinstance(val, dict) and val.get("rfid") == rfid_code:
            return val
    return None

@app.route("/status")
def status():
    data = load_songs()
    rfid = data.get("last_read_rfid", "")
    match = find_song_by_rfid(data, rfid)
    status = {
        "rfid": rfid,
        "status": "ready" if match and os.path.exists(os.path.join(STORAGE_DIR, match["filename"])) else "missing"
    }
    return jsonify(status)

def download_song(song_id, url):
    filename = f"song_{song_id}.mp3"
    full_path = os.path.join(STORAGE_DIR, filename)
    cmd = (
        ["spotdl", "--output", full_path, url]
        if "spotify.com" in url
        else ["yt-dlp", "-x", "--audio-format", "mp3", url, "-o", full_path]
    )
    result = subprocess.run(cmd)

    songs = load_songs()
    if result.returncode == 0:
        songs[song_id]["status"] = "ready"
        songs[song_id]["filename"] = filename

        if "spotify.com" in url:
            songs[song_id]["title"] = filename
        else:
            meta = subprocess.run(["yt-dlp", "--get-title", url], capture_output=True, text=True)
            songs[song_id]["title"] = meta.stdout.strip() if meta.returncode == 0 else filename

        append_log(f"🎵 Lastet ned sang: {songs[song_id]['title']}")
    else:
        songs[song_id]["status"] = "error"
        append_log(f"❌ Nedlasting feilet: {url}")

    save_songs(songs)

@app.route("/")
def index():
    songs = load_songs()
    ip = request.host
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    log = load_log()
    return render_template("index.html", songs=songs, ip=ip, ip_address=ip_address, log=log)

@app.route("/add_url", methods=["POST"])
def add_url():
    url = request.form["url"].strip()
    if not is_valid_url(url):
        append_log("❌ Ugyldig URL lagt inn")
        return redirect("/")
    song_id = str(int(datetime.now().timestamp() * 1000))
    songs = load_songs()
    songs[song_id] = {"url": url, "status": "downloading"}
    save_songs(songs)
    append_log("🆕 Ny sang registrert")
    subprocess.Popen(["python3", __file__, "--download", song_id])
    return redirect("/")

@app.route("/play", methods=["POST"])
def play_song_route():
    song_id = request.form["song_id"]
    songs = load_songs()

    if song_id not in songs:
        append_log(f"❌ Ugyldig song_id: {song_id}")
        return redirect("/")

    filename = songs[song_id].get("filename")
    if not filename:
        append_log(f"❌ Ingen fil knyttet til song_id: {song_id}")
        return redirect("/")

    filepath = os.path.join(STORAGE_DIR, filename)

    if not os.path.exists(filepath):
        append_log(f"❌ Filen finnes ikke: {filepath}")
        return redirect("/")

    play_song(filepath)
    append_log(f"▶ Spiller: {songs[song_id].get('title', filename)}")

    return redirect("/")

# ... resten av ruter og funksjoner for delete, stop, set_volume osv. forblir uendret ...
