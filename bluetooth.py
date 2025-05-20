from flask import Blueprint, render_template, request, redirect # type: ignore
import subprocess

bluetooth_bp = Blueprint("bluetooth", __name__, template_folder="templates")

@bluetooth_bp.route("/bluetooth")
def bluetooth_page():
    paired_devices = get_paired_devices()
    return render_template("bluetooth.html", devices=paired_devices)

@bluetooth_bp.route("/bluetooth/scan")
def bluetooth_scan():
    try:
        output = subprocess.check_output(["bluetoothctl", "scan", "on"], timeout=5)
        return "🔍 Søker etter enheter..."
    except Exception as e:
        return f"❌ Feil ved scanning: {e}"

@bluetooth_bp.route("/bluetooth/pair", methods=["POST"])
def bluetooth_pair():
    addr = request.form["device"]
    try:
        subprocess.run(["bluetoothctl", "pair", addr], check=True)
        subprocess.run(["bluetoothctl", "trust", addr], check=True)
        subprocess.run(["bluetoothctl", "connect", addr], check=True)
        return redirect("/bluetooth")
    except Exception as e:
        return f"❌ Klarte ikke pare enhet {addr}: {e}"

@bluetooth_bp.route("/bluetooth/remove", methods=["POST"])
def bluetooth_remove():
    addr = request.form["device"]
    try:
        subprocess.run(["bluetoothctl", "remove", addr], check=True)
        return redirect("/bluetooth")
    except Exception as e:
        return f"❌ Klarte ikke fjerne enhet {addr}: {e}"

def get_paired_devices():
    try:
        output = subprocess.check_output(["bluetoothctl", "paired-devices"], text=True)
        devices = []
        for line in output.strip().split("\n"):
            if line.startswith("Device"):
                parts = line.split(" ", 2)
                if len(parts) == 3:
                    addr, name = parts[1], parts[2]
                    devices.append({"addr": addr, "name": name})
        return devices
    except Exception as e:
        return [{"addr": "N/A", "name": f"Feil: {e}"}]