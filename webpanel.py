from flask import Flask, request, redirect, render_template
import os
import subprocess
import socket
from datetime import datetime
from utils import append_log, load_log, load_songs, save_songs

app = Flask(__name__)
STORAGE_DIR = "/home/magic/RFIDMusicBox/mp3"

def is_valid_url(url):
    return url.startswith("http") and (
        "youtube.com" in url or "spotify.com" in url or "youtu.be" in url
    )

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
def play_song():
    song_id = request.form["song_id"]
    songs = load_songs()
    if song_id in songs:
        filepath = os.path.join(STORAGE_DIR, songs[song_id]["filename"])
        subprocess.Popen(["mpv", "--no-video", filepath])
        append_log(f"▶ Spiller: {songs[song_id].get('title', song_id)}")
    return redirect("/")

@app.route("/delete_song", methods=["POST"])
def delete_song():
    song_id = request.form["song_id"]
    songs = load_songs()
    song = songs.get(song_id)
    if song and song.get("filename"):
        path = os.path.join(STORAGE_DIR, song["filename"])
        if os.path.exists(path):
            os.remove(path)
    if song_id in songs:
        append_log(f"🗑 Slettet sang: {songs[song_id].get('title', song_id)}")
        del songs[song_id]
        save_songs(songs)
    return redirect("/")

@app.route("/link_rfid", methods=["POST"])
def link_rfid():
    song_id = request.form["song_id"]
    songs = load_songs()
    rfid = songs.get("last_read_rfid")
    if not rfid:
        append_log("⚠️ Ingen RFID skannet")
        return redirect("/")

    for sid, info in songs.items():
        if sid == "last_read_rfid":
            continue
        if isinstance(info, dict) and info.get("rfid") == rfid and sid != song_id:
            append_log("⚠️ RFID allerede i bruk")
            return redirect("/")

    songs[song_id]["rfid"] = rfid
    append_log(f"🔗 Knyttet RFID {rfid} til {songs[song_id].get('title', song_id)}")
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

@app.route("/help")
def help():
    return render_template("help.html")

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--download":
        sid = sys.argv[2]
        songs = load_songs()
        if sid in songs:
            download_song(sid, songs[sid]["url"])
    else:
        app.run(host="0.0.0.0", port=5000)
