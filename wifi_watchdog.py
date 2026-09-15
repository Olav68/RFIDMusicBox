# wifi_watchdog.py - Sjekker om Pi-en har internett. Hvis ikke, oppretter
# den sitt eget WiFi-nett (hotspot) slik at webpanelet er nåbart uten
# ekisterende nettverk, og man kan koble den til riktig WiFi via /wifi.
import subprocess
import time
from utils import append_log

HOTSPOT_SSID = "RFIDMusicBox-Oppsett"
HOTSPOT_PASSWORD = "musikkboks123"
HOTSPOT_CONNECTION_NAME = "RFIDMusicBox-Hotspot"
WIFI_INTERFACE = "wlan0"
CHECK_INTERVAL = 30
STARTUP_GRACE_PERIOD = 20  # gi vanlig WiFi tid til å koble til før vi vurderer hotspot


def has_internet():
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "CONNECTIVITY", "general"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == "full"
    except Exception as e:
        append_log(f"❌ Klarte ikke sjekke nettstatus: {e}")
        return False


def is_hotspot_active():
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME", "connection", "show", "--active"],
            capture_output=True, text=True, timeout=5
        )
        return HOTSPOT_CONNECTION_NAME in result.stdout.splitlines()
    except Exception as e:
        append_log(f"❌ Klarte ikke sjekke hotspot-status: {e}")
        return False


def start_hotspot():
    append_log(f"📡 Ingen internettforbindelse - starter eget WiFi-nett: {HOTSPOT_SSID}")
    try:
        subprocess.run([
            "nmcli", "device", "wifi", "hotspot",
            "ifname", WIFI_INTERFACE,
            "con-name", HOTSPOT_CONNECTION_NAME,
            "ssid", HOTSPOT_SSID,
            "password", HOTSPOT_PASSWORD,
        ], check=True)
        append_log(f"✅ Eget WiFi-nett aktivt: {HOTSPOT_SSID} (passord: {HOTSPOT_PASSWORD})")
    except Exception as e:
        append_log(f"❌ Klarte ikke starte eget WiFi-nett: {e}")


def stop_hotspot():
    append_log("📡 Internett funnet - stopper eget WiFi-nett")
    try:
        subprocess.run(["nmcli", "connection", "down", HOTSPOT_CONNECTION_NAME], check=True)
    except Exception as e:
        append_log(f"❌ Klarte ikke stoppe eget WiFi-nett: {e}")


def main():
    append_log("🔌 Starter WiFi-overvåker")
    time.sleep(STARTUP_GRACE_PERIOD)

    while True:
        try:
            if has_internet():
                if is_hotspot_active():
                    stop_hotspot()
            else:
                if not is_hotspot_active():
                    start_hotspot()
        except Exception as e:
            append_log(f"💥 Feil i WiFi-overvåker: {e}")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
