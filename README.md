# Ola's Magiske Spilleboks 🎶✨

Et Raspberry Pi-basert musikksystem for barn, som spiller av sanger når man skanner et RFID-kort. Sanger kan kobles til kort via et enkelt webgrensesnitt. Alt lagres lokalt og kan brukes offline.

## 📦 Funksjoner

- 🎵 Skann et RFID-kort → spill av tilkoblet MP3-fil
- 🌐 Webgrensesnitt for administrasjon av sanger og kort
- ✅ Automatisk nedlasting av MP3 fra YouTube/Spotify
- 💾 Støtte for lagring på SD-kort eller lokal disk
- 🔊 Volumkontroll og avspillingsstyring
- 🪪 Koble eller fjern RFID-koder enkelt
- 📜 Logger aktivitet og systemstatus

## 🖥️ Systemkrav

- Raspberry Pi (anbefalt Pi 3 eller nyere)
- Python 3.10+
- RFID-leser (USB-emulerende, f.eks. 13.56 MHz USB)
- Høyttaler (Bluetooth eller jack)

## 🚀 Installering

```bash
sudo apt update && sudo apt install python3-pip git unzip -y
git clone https://github.com/Olav68/RFIDMusicBox.git
cd RFIDMusicBox
pip install -r requirements.txt

🔧 Oppsett av systemtjenester
Systemet starter automatisk ved oppstart via systemd:

sudo cp rfid_webpanel.service /etc/systemd/system/
sudo cp rfid_listener.service /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl enable rfid_webpanel
sudo systemctl enable rfid_listener
sudo systemctl start rfid_webpanel
sudo systemctl start rfid_listener

Filstruktur
RFIDMusicBox/
├── main.py                 # Lydavspiller (lytter på RFID)
├── webpanel.py            # Flask-basert kontrollpanel
├── utils.py               # Felles verktøy (logging, lagring)
├── templates/             # HTML-filer
├── static/                # PDF-manual, evt. CSS/filer
├── mp3/                   # Lokalt lagrede MP3-filer
├── songs.json             # Koblede sanger og RFID-koder
├── config.json            # Innstillinger (lagringssti mm.)
└── activity_log.json      # Logg over aktivitet
