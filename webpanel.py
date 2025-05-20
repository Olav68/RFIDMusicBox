from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import json
import subprocess
from utils import append_log, load_log, load_songs, save_songs

app = Flask(__name__)

@app.route("/")
def index():
    songs = load_songs()
    return render_template("index.html", songs=songs)

@app.route("/wifi")
def wifi_settings():
    connected_ssid = get_connected_ssid()
    networks = scan_wifi_networks()
    return render_template("wifi.html", connected_ssid=connected_ssid, networks=networks)

def get_connected_ssid():
    try:
        result = subprocess.check_output("nmcli -t -f active,ssid dev wifi", shell=True).decode("utf-8")
        for line in result.splitlines():
            active, ssid = line.split(":")
            if active == "yes":
                return ssid
    except Exception as e:
        append_log(f"Feil ved henting av tilkoblet SSID: {e}")
    return None

def scan_wifi_networks():
    try:
        result = subprocess.check_output("nmcli -t -f ssid,signal dev wifi", shell=True).decode("utf-8")
        networks = []
        for line in result.splitlines():
            if line:
                parts = line.split(":")
                if len(parts) >= 2:
                    ssid, signal = parts[0], parts[1]
                    if ssid:
                        networks.append({"ssid": ssid, "signal": signal})
        return networks
    except Exception as e:
        append_log(f"Feil ved skanning av nettverk: {e}")
    return []

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3 and sys.argv[1] == "--download":
        sid = sys.argv[2]
        songs = load_songs()
        if sid in songs:
            download_song(sid, songs[sid]["url"])
    else:
        app.run(host="0.0.0.0", port=5000)