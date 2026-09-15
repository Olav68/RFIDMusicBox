# Ola's Magiske Spilleboks 🎶✨

Et Raspberry Pi-basert musikksystem for barn, som spiller av sanger når man skanner et RFID-kort. Sanger og spillelister kobles til kort via et enkelt webgrensesnitt. Alt lagres lokalt og kan brukes offline.

## 📦 Funksjoner

- 🎵 Skann et RFID-kort → spill av tilkoblet sang eller spilleliste
- 🌐 Webgrensesnitt for administrasjon av sanger, spillelister og kort
- ✅ Automatisk nedlasting av MP3 fra YouTube (enkeltsanger og spillelister)
- 🔵 Søk etter, par og koble til nye Bluetooth-høyttalere fra panelet
- 🔈 Velg aktiv lydutgang (f.eks. Bluetooth-høyttaler) fra panelet
- 🔊 Volumkontroll og avspillingsstyring
- 🪪 Koble eller fjern RFID-koder enkelt
- 🔘 Fysiske GPIO-knapper for volum opp/ned, stopp og spill av igjen
- 📶 Koble til WiFi fra panelet, med automatisk oppsetts-hotspot hvis Pi-en mangler nett
- 🔄 Hent oppdatert kode fra git manuelt fra panelet, eller automatisk ved oppstart
- 📜 Logger aktivitet og systemstatus

## 🖥️ Systemkrav

- Raspberry Pi (anbefalt Pi 3 eller nyere — se maskinvarelisten under for konkret anbefaling)
- Python 3.10+
- RFID-leser (USB-emulerende tastatur, f.eks. 13.56 MHz USB)
- `mpv`, `yt-dlp`, `ffmpeg`, PulseAudio (`pactl`) og BlueZ (`bluetoothctl`) installert på systemet
- NetworkManager (`nmcli`) må styre WiFi-grensesnittet — standard på Raspberry Pi OS Bookworm; på eldre
  utgaver må det installeres og `dhcpcd` sin kontroll over `wlan0` deaktiveres
- Høyttaler (Bluetooth, jack eller innebygd via I2S — se under)

## 🧰 Maskinvareliste (BOM)

Full delliste for å bygge en fysisk boks fra bunnen av, inkludert innebygd høyttaler, fysiske knapper og
3D-printet hus (f.eks. et Phoniebox-design printet på en Bambu A1). Nøyaktig antall skruer/innsatser/magneter
avhenger av hvilket husdesign du velger — sjekk delelisten som følger med den konkrete 3D-modellen.

### Elektronikk

| Del | Eksempel/spesifikasjon | Antall | Butikk (Norden) |
|---|---|---|---|
| Raspberry Pi | [Pi Zero 2 W, **uten** header](https://www.electrokit.com/en/raspberry-pi-zero-2-w-no-pin-header) — du lodder header selv, se under | 1 | Electrokit |
| GPIO-header | [Stiftlist 2,54mm 2×20-pin, rett](https://www.electrokit.com/en/stiftlist-2.54mm-2x20p) — loddes fast på Pi-en | 1 | Electrokit |
| microSD-kort | [Sandisk Ultra 32GB SDHC](https://kjell.com/se/produkter/dator/minneskort/sandisk-ultra-micro-sd-kort-32-gb-sdhc-p90992) | 1 | Kjell & Company |
| Strømforsyning | [5,1V/2,5A micro-USB, offisiell type](https://www.electrokit.com/en/raspberry-pi-4-stromforsorjning-5v-2.5a-micro-usb-vit) | 1 | Electrokit |
| RFID-leser | [USB-leser 13,56MHz, keyboard-emulering, 50×20×5mm](https://www.electrokit.com/en/rfid-lasare-usb-13.56mhz) | 1 | Electrokit — må matche `DEVICE_NAME` i `rfid_input_listener.py` |
| Micro-USB OTG-adapter | [Luxorparts OTG-adapter m/kabel](https://www.kjell.com/se/produkter/mobilt/ladda-koppla/kablar-adaptrar/micro-usb-kablar/luxorparts-otg-adapter-med-kabel-02-m-p92967) | 1 | Kjell & Company — kun nødvendig ved Pi Zero 2 W |
| I2S-forsterker | [3W stereo I2S-forsterker-bonnet for Raspberry Pi](https://www.electrokit.com/en/3w-stereo-speaker-bonnet) (Adafruit MAX98357-basert, 65×30×7,2mm) | 1 | Electrokit — plugges rett på GPIO-headeren, leveres med løs 2×20-hylslist du selv lodder på bonneten |
| Høyttaler | [4Ω 3W, ferdig i boks m/JST-kontakt, 70×30×17mm](https://www.electrokit.com/en/hogtalare-4ohm-3w-i-lada-med-jst-kontakt) | 1 (2 ved stereo-hus) | Electrokit — kobles til bonnetens skrueterminaler |
| Trykknapper | Momentan trykknapp ø12mm — [svart](https://www.electrokit.com/tryckknapp-12.2mm-1-pol-off-onsvart) / [gul](https://www.electrokit.com/en/tryckknapp-12.2mm-1-pol-off-ongul) / [rød](https://www.electrokit.com/tryckknapp-12.2mm-1-pol-off-on-rod) | 4 (ulike farger anbefalt) | Electrokit — se "Fysiske knapper" |
| Loddetråd til knapper | Tynn fleksibel monteringstråd + krympestrømpe | Etter behov | Siden du lodder selv, trenger du ikke dupont-jumperkabler — se lodde-notat under |

**Lodde-notat:** Bonneten dekker alle 40 GPIO-pinnene fysisk når den er plugget på headeren, men loddesiden (undersiden) av hver pinne er fortsatt fritt tilgjengelig for lodding — akkurat som med enhver gjennomhulls-header. Når du lodder GPIO-headeren fast på Pi-en, tini samtidig en tynn ledning direkte på loddesiden av pinnene for BCM 5, 6, 13, 19 og en GND-pinne (se pin-oversikten i "Fysiske knapper") og før disse ledningene til knappene. Det trengs ingen dupont-kontakter eller ekstra høy/stackbar header — en vanlig 2×20-header er nok, siden knappene kobles permanent med loddepunkt, ikke pluggbart.

### RFID-brikker (til å skanne)

| Type | Spesifikasjon | Butikk (Norden) |
|---|---|---|
| Kort, 10-pack | [13,56 MHz Mifare 1k, kredittkortformat](https://www.electrokit.com/en/rfid-tag-13.56mhz-1kb-eeprom-10-pack) | Electrokit |
| Enkeltkort | [13,56 MHz Mifare-kompatibelt](https://www.electrokit.com/en/rfid-tag-mifare-13.56mhz-kreditkort) | Electrokit |
| Klistremerke ø25mm | [13,56 MHz Mifare-kompatibel etikett](https://www.electrokit.com/en/rfid/nfc-etikett-13.56mhz-mifare-kompatibel-25mm) | Electrokit — kan limes på tegninger/figurer barna lager selv |
| Nøkkelbrikke (fob) | [13,56 MHz Mifare-kompatibel, flere farger](https://www.electrokit.com/en/rfid/nfc-tagg-13.56mhz-1k-mifare-kompatibel-rod) | Electrokit — robust, tåler å bli mishandlet av barn |

**Viktig:** frekvensen på tag/kort/brikke må matche frekvensen leseren støtter (13,56 MHz vs. 125 kHz) —
sjekk leserens spesifikasjon før kjøp av tags. Alt over er 13,56 MHz og matcher USB-leseren anbefalt over.

### Fysiske mål (sjekk mot valgt 3D-print-design)

Bambu Studio/slicere kan ikke sjekke dette automatisk — mål komponentene mot det interne rommet og
utsparingene (RFID-lomme, høyttalergrille, knappehull) i den konkrete modellen du printer, **før** du printer:

| Komponent | Mål |
|---|---|
| Pi Zero 2 W (kretskort) | 65 × 30 mm |
| Pi + header + I2S-bonnet (stables oppå) | 65 × 30 mm, ~20 mm total høyde inkl. header og bonnet |
| RFID-leser | 50 × 20 × 5 mm |
| Høyttaler i boks | 70 × 30 × 17 mm, monteringshull i mønster 63 × 24 mm (ø3,4mm hull) |
| Trykknapp | ø12mm hull i panel, ~20–28mm dybde bak panelet |

Jeg fikk ikke lest de eksakte interne målene på de foreslåtte MakerWorld/Printables-modellene direkte (siden
blokkerer automatisk nedlasting av sidetekst) — åpne modellen i Bambu Studio og sammenlign mot tabellen over,
eller del skjermbilde/mål fra modellsiden så kan jeg hjelpe deg å vurdere om det passer.

### Montering / 3D-print

| Del | Spesifikasjon | Antall | Butikk (Norden) |
|---|---|---|---|
| M3 skrue-/muttersett | [1300 deler, blandede lengder](https://www.clasohlson.com/no/Skrue--og-muttersett-1300-deler/p/40-7042) | 1 sett | Clas Ohlson |
| M3 varmesett-innsatser | [Messing, M3×4mm, 50-pack](https://www.electrokit.com/en/ganginsats-m3-x-4mm-50-pack) + [monteringsverktøy til loddebolt](https://www.electrokit.com/en/verktyg-for-ganginsats-m3) | 8–12 innsatser | Electrokit |
| Neodym-magneter | [12mm, 6-pack](https://kjell.com/se/produkter/hem-kontor-fritid/gadgets/neodymmagnet-12-mm-6-pack-p50071) | 4–6 | Kjell & Company — se merknad under |
| Skiver/avstandsstykker | M3 | Etter behov | Inngår i skrue-/muttersettet over |

**Merknad om magneter:** ingen store nordiske butikker fører den lille 5×2mm-størrelsen fra den originale
listen — nærmeste tilgjengelige er 8mm eller 12mm. Enten tilpasser du magnetlommen i 3D-printet til denne
størrelsen (juster i slicer/CAD før print), eller bestiller 5×2mm spesifikt fra f.eks. Amazon/AliExpress om
nøyaktig størrelse er viktig for det valgte husdesignet.

## 🚀 Installering

```bash
sudo apt update && sudo apt install python3-pip git mpv ffmpeg unzip -y
git clone https://github.com/Olav68/RFIDMusicBox.git
cd RFIDMusicBox
pip install -r requirements.txt
```

## 🔧 Oppsett av systemtjenester

Systemet består av seks uavhengige systemd-tjenester:

- `rfid_auto_update` — sjekker git for oppdatert kode én gang ved oppstart, før de andre tjenestene starter; se under
- `rfid_input_listener` — leser RFID-koder fra USB-leseren
- `rfid_trigger_listener` — spiller av sang/spilleliste når et nytt kort skannes
- `rfid_webpanel` — Flask-basert kontrollpanel på port 5000
- `rfid_wifi_watchdog` — sjekker jevnlig om Pi-en har internett; se under
- `rfid_button_listener` — leser fysiske GPIO-knapper; se under

Installer og aktiver alle seks med:

```bash
sudo bash scripts/installer_tjenester.sh
```

Dette kopierer filene i `services/` til `/etc/systemd/system/` og aktiverer dem, og setter opp en `sudoers`-regel
som gir brukeren passordløs tilgang til nøyaktig `systemctl reboot` (se under). Kjør samme script på nytt etter
en `git pull` for å oppdatere en kjørende installasjon.

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

## 🔵 Bluetooth-høyttalere

Siden `/bluetooth` i panelet lar deg:

- Søke etter nye enheter (tar ca. 8 sekunder - panelet svarer ikke før søket er ferdig)
- Pare, stole på og koble til en funnet enhet med ett trykk
- Koble til en allerede paret enhet på nytt (f.eks. etter at den har vært av)
- Sette en tilkoblet Bluetooth-høyttaler som standard lydutgang direkte fra siden
- Fjerne (glemme) en paret enhet

Dette bruker `bluetoothctl` direkte og forutsetter at BlueZ er installert og kjører (`bluetoothd`), som er
standard på Raspberry Pi OS med innebygd eller USB-Bluetooth. Den samme "velg standard lydutgang"-dropdownen
på forsiden fantes allerede fra før og fungerer uavhengig av denne siden - `/bluetooth` gjør det i tillegg
mulig å pare en helt ny høyttaler i utgangspunktet.

## 🔘 Fysiske knapper

`rfid_button_listener` leser fire knapper koblet til Pi-ens GPIO-pinner (BCM-nummerering) og gjør det samme
som de tilsvarende knappene i webpanelet:

| Knapp | BCM-pin | Handling |
|---|---|---|
| Volum opp | 6 | `amixer sset Master 5%+` |
| Volum ned | 5 | `amixer sset Master 5%-` |
| Stopp | 13 | Stopper avspilling (som "⏹" i panelet) |
| Spill av igjen | 19 | Spiller av sangen/spillelisten koblet til sist skannede RFID-kort på nytt |

Hver knapp kobles mellom valgt GPIO-pin og en GND-pin (f.eks. pin 6, 9, 14, 20 eller 25 på headeren) - `gpiozero`
bruker Pi-ens interne pull-up-motstand, så ingen eksterne komponenter er nødvendig utover selve knappen.
Pinnenumrene er konstanter øverst i `gpio_button_listener.py` og kan endres der om du kobler knappene til andre
pinner.

## 🔄 Oppdatering av kode

To måter å hente ny kode fra git på:

- **Automatisk ved oppstart:** `rfid_auto_update` kjører `scripts/git_update.sh` én gang før de andre
  tjenestene starter. Git-kallene er tidsbegrenset (15s) slik at manglende nett ikke forsinker oppstarten -
  tjenestene starter uansett med den koden som allerede ligger på disk.
- **Manuelt fra panelet:** knappen "🔄 Sjekk etter oppdatering" på forsiden kjører samme script. Finnes det en
  ny versjon, hentes den (`git reset --hard origin/main`) og **Pi-en restarter seg selv** noen sekunder senere
  for å ta den i bruk. Er koden allerede oppdatert, skjer ingenting utover en loggmelding.

Restarten skjer via `sudo systemctl reboot`, som webpanel-prosessen (kjører ikke-interaktivt, kan ikke skrive
inn et passord) trenger passordløs tilgang til. `scripts/installer_tjenester.sh` setter opp nøyaktig denne ene
sudoers-regelen automatisk - ingen bred sudo-tilgang gis.

## 📁 Filstruktur

```
RFIDMusicBox/
├── webpanel.py                  # Flask-basert kontrollpanel
├── rfid_input_listener.py       # Leser RFID-koder fra USB-leseren
├── rfid_trigger_listener.py     # Spiller av sang/spilleliste ved nytt RFID-kort
├── wifi_watchdog.py             # Starter eget WiFi-nett hvis Pi-en mangler internett
├── gpio_button_listener.py      # Leser fysiske GPIO-knapper (volum, stopp, spill av igjen)
├── utils.py                     # Felles verktøy (logging, lagring, avspilling, lydenheter)
├── services/                    # systemd-enhetsfiler for de seks tjenestene
├── scripts/                     # Installasjons- og driftsscript
├── templates/                   # HTML-filer for webpanelet
├── static/                      # PDF-bruksanvisning
├── mp3/                         # Nedlastede sanger og spillelister (mappen er i git, innholdet er git-ignorert)
├── songs.json                   # Koblede sanger og RFID-koder (ikke i git)
└── activity_log.json            # Logg over aktivitet (ikke i git)
```
