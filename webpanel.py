from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
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
    download_youtube_playlist
)

app = Flask(__name__)

STORAGE_DIR = "/home/magic/programmer/RFIDMusicBox/mp3"
SONGS_FILE = "/home/magic/programmer/RFIDMusicBox/songs.json"
MUSIC_DIR = "/home/magic/programmer/RFIDMusicBox/music"

def is_valid_url(url):
    return url.startswith("http") and (
        "youtube.com" in url or "youtu.be" in url
    )

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
    valid = False
    if match:
        if match.get("type") == "song" and "filename" in match:
            valid = os.path.exists(os.path.join(STORAGE_DIR, match["filename"]))
        elif match.get("type") == "playlist" and "playlist_dir" in match:
            folder_path = os.path.join(STORAGE_DIR, match["playlist_dir"])
            valid = os.path.exists(folder_path) and any(f.endswith(".mp3") for f in os.listdir(folder_path))
    status = {
        "rfid": rfid,
        "status": "ready" if valid else "missing"
    }
    return jsonify(status)

def download_song(song_id, url):
    songs = load_songs()
    if is_youtube_playlist(url):
        playlist_dir = f"playlist_{song_id}"
        full_path = os.path.join(STORAGE_DIR, playlist_dir)
        os.makedirs(full_path, exist_ok=True)
        success = download_youtube_playlist(url, full_path)
        if success:
            songs[song_id]["status"] = "ready"
            songs[song_id]["playlist_dir"] = playlist_dir
            append_log(f"📥 Lastet ned spilleliste til: {playlist_dir}")
        else:
            songs[song_id]["status"] = "error"
            append_log(f"❌ Feil ved nedlasting av spilleliste: {url}")
    else:
        filename = f"song_{song_id}.mp3"
        full_path = os.path.join(STORAGE_DIR, filename)
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", url, "-o", full_path]
        result = subprocess.run(cmd)
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
    song_type = "playlist" if is_youtube_playlist(url) else "song"
    songs[song_id] = {"url": url, "status": "downloading", "type": song_type}
    save_songs(songs)
    append_log("🆕 Ny sang eller liste registrert")
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
        files = sorted(f for f in os.listdir(folder) if f.endswith(".mp3"))
        for file in files:
            play_song(os.path.join(folder, file))
    elif song.get("type") == "song" and "filename" in song:
        filepath = os.path.join(STORAGE_DIR, song["filename"])
        if os.path.exists(filepath):
            play_song(filepath)
            append_log(f"▶ Spiller: {song.get('title', filepath)}")
        else:
            append_log(f"❌ Fil ikke funnet: {filepath}")

    return redirect("/")
