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
    download_youtube_playlist,
    play_playlist,
    list_audio_devices_with_friendly_names as list_audio_devices,
    get_current_default_sink  # ← riktig funksjon her
)

#13:11
app = Flask(__name__)

STORAGE_DIR = "/home/magic/programmer/RFIDMusicBox/mp3"
SONGS_FILE = "/home/magic/programmer/RFIDMusicBox/songs.json"
MUSIC_DIR = "/home/magic/programmer/RFIDMusicBox/music"

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

@@app.route("/")
def index():
    songs = load_songs()
    ip = request.host
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    log = load_log()
    audio_devices = list_audio_devices()
    current_sink = get_current_default_sink()

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
        current_sink_friendly=current_sink_friendly
    )

@app.route("/set_default_device", methods=["POST"])
def set_default_device():
    sink_name = request.form.get("device_name")
    try:
        subprocess.run(["pactl", "set-default-sink", sink_name], check=True)
        append_log(f"🔊 Standard lydenhet satt til: {sink_name}")
    except Exception as e:
        append_log(f"❌ Feil ved setting av lydenhet: {e}")
    return redirect("/")

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
    return jsonify({
        "rfid": rfid,
        "status": "ready" if valid else "missing"
    })

@app.route("/log")
def log():
    return jsonify(load_log())

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
        play_playlist(folder)
    elif song.get("type") == "song" and "filename" in song:
        filepath = os.path.join(STORAGE_DIR, song["filename"])
        play_song(filepath)
    else:
        append_log("⚠️ Ukjent sangtype eller mangler fil/dir")

    return redirect("/")

@app.route("/delete_song", methods=["POST"])
def delete_song():
    song_id = request.form["song_id"]
    songs = load_songs()
    song = songs.get(song_id)

    # Slett MP3-fil hvis den finnes
    if song and "filename" in song:
        filepath = os.path.join(STORAGE_DIR, song["filename"])
        if os.path.exists(filepath):
            os.remove(filepath)
    
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

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--download":
        sid = sys.argv[2]
        songs = load_songs()
        if sid in songs:
            download_song(sid, songs[sid]["url"])
    else:
        append_log("🌍 Starter webpanel på port 5000")
        app.run(host="0.0.0.0", port=5000)