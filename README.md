# Ola's Magiske Spilleboks 🎶✨

Et Raspberry Pi-basert musikksystem for barn, som spiller av sanger når man skanner et RFID-kort. Sanger og spillelister kobles til kort via et enkelt webgrensesnitt. Alt lagres lokalt og kan brukes offline.

## 📦 Funksjoner

- 🎵 Skann et RFID-kort → spill av tilkoblet sang eller spilleliste
- 🌐 Webgrensesnitt for administrasjon av sanger, spillelister og kort
- ✅ Automatisk nedlasting av MP3 fra YouTube (enkeltsanger og spillelister)
- 🔈 Velg aktiv lydutgang (f.eks. Bluetooth-høyttaler) fra panelet
- 🔊 Volumkontroll og avspillingsstyring
- 🪪 Koble eller fjern RFID-koder enkelt
- 📜 Logger aktivitet og systemstatus

## 🖥️ Systemkrav

- Raspberry Pi (anbefalt Pi 3 eller nyere)
- Python 3.10+
- RFID-leser (USB-emulerende tastatur, f.eks. 13.56 MHz USB)
- `mpv`, `yt-dlp` og PulseAudio (`pactl`) installert på systemet
- Høyttaler (Bluetooth eller jack)

## 🚀 Installering

```bash
sudo apt update && sudo apt install python3-pip git mpv unzip -y
git clone https://github.com/Olav68/RFIDMusicBox.git
cd RFIDMusicBox
pip install -r requirements.txt
```

## 🔧 Oppsett av systemtjenester

Systemet består av tre uavhengige systemd-tjenester som starter automatisk ved oppstart:

- `rfid_input_listener` — leser RFID-koder fra USB-leseren
- `rfid_trigger_listener` — spiller av sang/spilleliste når et nytt kort skannes
- `rfid_webpanel` — Flask-basert kontrollpanel på port 5000

Installer og aktiver alle tre med:

```bash
sudo bash scripts/installer_tjenester.sh
```

Dette kopierer filene i `services/` til `/etc/systemd/system/` og aktiverer dem. Kjør samme script på nytt etter en `git pull` for å oppdatere en kjørende installasjon.

## 📁 Filstruktur

```
RFIDMusicBox/
├── webpanel.py                  # Flask-basert kontrollpanel
├── rfid_input_listener.py       # Leser RFID-koder fra USB-leseren
├── rfid_trigger_listener.py     # Spiller av sang/spilleliste ved nytt RFID-kort
├── utils.py                     # Felles verktøy (logging, lagring, avspilling, lydenheter)
├── services/                    # systemd-enhetsfiler for de tre tjenestene
├── scripts/                     # Installasjons- og driftsscript
├── templates/                   # HTML-filer for webpanelet
├── static/                      # PDF-bruksanvisning
├── mp3/                         # Lokalt lagrede sanger og spillelister (ikke i git)
├── songs.json                   # Koblede sanger og RFID-koder (ikke i git)
└── activity_log.json            # Logg over aktivitet (ikke i git)
```
