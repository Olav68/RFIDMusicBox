# rfid_trigger_listener.py
import time
import os
from utils import load_songs, append_log, play_song, play_playlist, find_song_by_rfid

SONGS_FILE = "/home/magic/programmer/RFIDMusicBox/songs.json"
STORAGE_DIR = "/home/magic/programmer/RFIDMusicBox/mp3"
LAST_RFID_FILE = "/home/magic/programmer/RFIDMusicBox/.last_rfid_seen.txt"

# Hvor lenge samme kort ignoreres etter forrige avspilling. Beskytter mot at et
# kort som blir liggende nær leseren (mange lesere skanner kontinuerlig, ikke
# bare én gang per "trykk") trigger avspilling på nytt gang på gang. Etter
# denne pausen kan samme kort skannes på nytt for å spille av igjen.
REPLAY_DEBOUNCE_SECONDS = 3

def get_last_processed():
    if os.path.exists(LAST_RFID_FILE):
        with open(LAST_RFID_FILE, "r") as f:
            content = f.read().strip()
        if "|" in content:
            rfid, _, scan_time = content.partition("|")
            try:
                return rfid, float(scan_time)
            except ValueError:
                return rfid, 0.0
        # Eldre format uten tidsstempel (fra før denne funksjonen fantes)
        return content, 0.0
    return None, 0.0

def set_last_processed(rfid_code, scan_time):
    with open(LAST_RFID_FILE, "w") as f:
        f.write(f"{rfid_code}|{scan_time}")

def play_for_rfid(data, rfid_code):
    song = find_song_by_rfid(data, rfid_code)
    if song:
        if song.get("type") == "playlist" and "playlist_dir" in song:
            folder = os.path.join(STORAGE_DIR, song["playlist_dir"])
            append_log(f"▶ Spiller spilleliste: {song.get('title', folder)}")
            play_playlist(folder)
        elif "filename" in song:
            filepath = os.path.join(STORAGE_DIR, song["filename"])
            if os.path.exists(filepath):
                append_log(f"▶ Spiller: {song.get('title', filepath)}")
                play_song(filepath)
            else:
                append_log(f"❌ Fil mangler: {filepath}")
        else:
            append_log(f"❌ Ingen gyldig kilde for sang knyttet til RFID: {rfid_code}")
    else:
        append_log(f"🚫 Ingen sang knyttet til RFID: {rfid_code}")

def main():
    append_log("🔌 RFID trigger-lytter startet")
    while True:
        try:
            data = load_songs()
            current_rfid = data.get("last_read_rfid", "").strip()
            # None (ikke 0) hvis feltet mangler - f.eks. rett etter oppgradering,
            # før noen har rukket å skanne et kort med den nye input-listeneren.
            current_scan_time = data.get("last_read_time")

            if not current_rfid:
                time.sleep(1)
                continue

            last_rfid, last_scan_time = get_last_processed()

            if current_scan_time is None:
                # Ingen tidsstempel å sammenligne med ennå (overgangstilstand) -
                # fall tilbake til den enkle "kun trigger hvis koden er endret"
                # slik det alltid har virket, i stedet for å risikere å trigge
                # på nytt hvert sekund uten noe reelt nytt signal å måle mot.
                if current_rfid == last_rfid:
                    time.sleep(1)
                    continue
                append_log(f"📻 Ny RFID skannet: {current_rfid}")
                set_last_processed(current_rfid, time.time())
                play_for_rfid(data, current_rfid)
                time.sleep(1)
                continue

            # Ingen ny fysisk skanning siden sist vi sjekket - ikke gjør noe,
            # uansett hvor lenge det er siden (unngår at samme sang starter på
            # nytt bare fordi klokken har gått, uten at kortet er skannet igjen).
            if current_scan_time <= last_scan_time:
                time.sleep(1)
                continue

            is_lingering_duplicate = (
                current_rfid == last_rfid
                and (current_scan_time - last_scan_time) < REPLAY_DEBOUNCE_SECONDS
            )

            if is_lingering_duplicate:
                # Samme kort lest på nytt rett etter forrige gang - trolig
                # fortsatt liggende ved leseren. Oppdater tidsstempelet så vi
                # ikke trigger på denne igjen, men ikke spill av på nytt.
                set_last_processed(current_rfid, current_scan_time)
                time.sleep(1)
                continue

            append_log(f"📻 Ny RFID skannet: {current_rfid}")
            set_last_processed(current_rfid, current_scan_time)
            play_for_rfid(data, current_rfid)

            time.sleep(1)

        except Exception as e:
            append_log(f"💥 Feil i RFID trigger-lytter: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()
