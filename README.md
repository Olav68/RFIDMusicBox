# Ola's Magiske Spilleboks 🎶✨

Et Raspberry Pi-basert musikksystem for barn, som spiller av sanger når man skanner et RFID-kort. Sanger og spillelister kobles til kort via et enkelt webgrensesnitt. Alt lagres lokalt og kan brukes offline.

## 📦 Funksjoner

- 🎵 Skann et RFID-kort → spill av tilkoblet sang eller spilleliste
- 🌐 Webgrensesnitt for administrasjon av sanger, spillelister og kort
- ✅ Automatisk nedlasting av MP3 fra YouTube (enkeltsanger og spillelister)
- 🔈 Velg aktiv lydutgang (f.eks. Bluetooth-høyttaler) fra panelet
- 🔊 Volumkontroll og avspillingsstyring
- 🪪 Koble eller fjern RFID-koder enkelt
- 📶 Koble til WiFi fra panelet, med automatisk oppsetts-hotspot hvis Pi-en mangler nett
- 📜 Logger aktivitet og systemstatus

## 🖥️ Systemkrav

- Raspberry Pi (anbefalt Pi 3 eller nyere)
- Python 3.10+
- RFID-leser (USB-emulerende tastatur, f.eks. 13.56 MHz USB)
- `mpv`, `yt-dlp`, `ffmpeg` og PulseAudio (`pactl`) installert på systemet
- NetworkManager (`nmcli`) må styre WiFi-grensesnittet — standard på Raspberry Pi OS Bookworm; på eldre
  utgaver må det installeres og `dhcpcd` sin kontroll over `wlan0` deaktiveres
- Høyttaler (Bluetooth eller jack)

## 🚀 Installering

```bash
sudo apt update && sudo apt install python3-pip git mpv ffmpeg unzip -y
git clone https://github.com/Olav68/RFIDMusicBox.git
cd RFIDMusicBox
pip install -r requirements.txt
```

## 🔧 Oppsett av systemtjenester

Systemet består av fire uavhengige systemd-tjenester som starter automatisk ved oppstart:

- `rfid_input_listener` — leser RFID-koder fra USB-leseren
- `rfid_trigger_listener` — spiller av sang/spilleliste når et nytt kort skannes
- `rfid_webpanel` — Flask-basert kontrollpanel på port 5000
- `rfid_wifi_watchdog` — sjekker jevnlig om Pi-en har internett; se under

Installer og aktiver alle fire med:

```bash
sudo bash scripts/installer_tjenester.sh
```

Dette kopierer filene i `services/` til `/etc/systemd/system/` og aktiverer dem. Kjør samme script på nytt etter en `git pull` for å oppdatere en kjørende installasjon.

## 📶 WiFi-oppsett og eget nett ved manglende tilkobling

`rfid_wifi_watchdog` sjekker hvert 30. sekund (etter en oppstartspause på 20 sekunder) om Pi-en har ekte
internettilgang (`nmcli -t -f CONNECTIVITY general`). Hvis ikke, oppretter den automatisk sitt eget WiFi-nett:

- **SSID:** `RFIDMusicBox-Oppsett`
- **Passord:** `musikkboks123`

(begge er konstanter øverst i `wifi_watchdog.py` og kan endres der)

Koble en telefon eller PC til dette nettverket og gå til `http://10.42.0.1:5000/wifi` (standard IP for
NetworkManager sin hotspot-modus) for å velge riktig hjemmenettverk og oppgi passord. Så snart Pi-en får ekte
internettilgang, stopper vaktbikkja det midlertidige nettet automatisk. Slår tilkoblingen feil (feil passord,
utenfor rekkevidde), vil vaktbikkja oppdage manglende internett igjen og starte oppsettsnettet på nytt slik at
du kan prøve igjen.

Wifi-siden i panelet (`/wifi`) viser skannede nettverk, men kan gi tomme resultater mens Pi-en selv kjører sitt
eget hotspot (radioen kan vanligvis ikke skanne og være hotspot samtidig) — bruk da feltet for manuell
tilkobling med nettverksnavn og passord.

## 📁 Filstruktur

```
RFIDMusicBox/
├── webpanel.py                  # Flask-basert kontrollpanel
├── rfid_input_listener.py       # Leser RFID-koder fra USB-leseren
├── rfid_trigger_listener.py     # Spiller av sang/spilleliste ved nytt RFID-kort
├── wifi_watchdog.py             # Starter eget WiFi-nett hvis Pi-en mangler internett
├── utils.py                     # Felles verktøy (logging, lagring, avspilling, lydenheter)
├── services/                    # systemd-enhetsfiler for de fire tjenestene
├── scripts/                     # Installasjons- og driftsscript
├── templates/                   # HTML-filer for webpanelet
├── static/                      # PDF-bruksanvisning
├── mp3/                         # Nedlastede sanger og spillelister (mappen er i git, innholdet er git-ignorert)
├── songs.json                   # Koblede sanger og RFID-koder (ikke i git)
└── activity_log.json            # Logg over aktivitet (ikke i git)
```
