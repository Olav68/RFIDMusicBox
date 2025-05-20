from flask import Blueprint, render_template, request, redirect
import subprocess

bluetooth_bp = Blueprint("bluetooth", __name__, template_folder="templates")


def get_paired_devices():
    try:
        output = subprocess.check_output(["bluetoothctl", "paired-devices"], text=True)
        devices = []
        for line in output.strip().split("\n"):
            parts = line.split(" ", 2)
            if len(parts) == 3:
                devices.append({"mac": parts[1], "name": parts[2]})
        return devices
    except Exception as e:
        return []


def scan_devices():
    try:
        subprocess.run(["bluetoothctl", "scan", "on"], timeout=3)
        output = subprocess.check_output(["bluetoothctl", "devices"], text=True)
        devices = []
        for line in output.strip().split("\n"):
            parts = line.split(" ", 2)
            if len(parts) == 3:
                devices.append({"mac": parts[1], "name": parts[2]})
        return devices
    except Exception as e:
        return []


@bluetooth_bp.route("/bluetooth")
def show_bluetooth():
    paired = get_paired_devices()
    discovered = scan_devices()
    return render_template("bluetooth.html", paired=paired, discovered=discovered)


@bluetooth_bp.route("/bluetooth/connect", methods=["POST"])
def connect_bluetooth():
    mac = request.form.get("mac")
    if mac:
        subprocess.run(["bluetoothctl", "pair", mac])
        subprocess.run(["bluetoothctl", "connect", mac])
        subprocess.run(["bluetoothctl", "trust", mac])
    return redirect("/bluetooth")


@bluetooth_bp.route("/bluetooth/remove", methods=["POST"])
def remove_bluetooth():
    mac = request.form.get("mac")
    if mac:
        subprocess.run(["bluetoothctl", "remove", mac])
    return redirect("/bluetooth")