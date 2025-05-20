1. Hvordan registrere en ny sang

Koble deg til boksen via nettleser:

Åpne nettleser på telefon, nettbrett eller PC

Gå til: http://magicmusicbox.local eller http://[IP-adresse]

Finn en sang-URL:

Spotify:

Åpne Spotify-appen

Finn sangen du vil bruke

Trykk "..." (mer), velg Del → Kopier lenke

YouTube:

Åpne YouTube

Finn ønsket video

Trykk "Del" → Kopier kobling

Lim inn sang-URL i webpanelet:

Eksempel:

YouTube: https://youtu.be/abc123

Spotify: https://open.spotify.com/track/...

Trykk "Lagre"

Sangen legges til i listen med gul hake: "Henter..."

Etter noen sekunder blir haken grønn: "Klar!"

Valgfritt:

Trykk "Spill" for å teste

Trykk "Slett" for å fjerne

2. Hvordan registrere en ny RFID-kode

Skann RFID-brikken på boksen

Et RFID-kort/skilt holdes inntil leseren

Du hører evt. bekreftelseslyd

Gå til webpanelet og finn sangen du vil koble til

Trykk på "Ny" i RFID-kolonnen

RFID-koden som nettopp ble skannet kobles til sangen

Når samme brikke skannes igjen:

Sangen spilles automatisk

3. Hvordan koble boksen til nytt WiFi-nettverk

Koble til boksen via kabel (eller eksisterende WiFi)

Åpne terminal via SSH:

ssh magic@magicmusicbox.local

Kør dette for å konfigurere nytt nettverk:

nmcli dev wifi list                # Se tilgjengelige nettverk
nmcli dev wifi connect "NETTVERKSNAVN" password "PASSORD"

Sjekk tilkobling:

ip a | grep wlan

Du kan nå bruke ny IP-adresse eller .local-navnet igjen

4. Hvordan koble til ny Bluetooth-høyttaler

Start Bluetooth-verktøyet:

bluetoothctl

Skru på søk og agent:

power on
agent on
default-agent
scan on

Finn høyttaleren:

Noter MAC-adressen, f.eks. B2:F9:2D:EE:95:9D

Par, støtt og koble til:

pair B2:F9:2D:EE:95:9D
trust B2:F9:2D:EE:95:9D
connect B2:F9:2D:EE:95:9D

Bekreft at lyden spilles via Bluetooth:

pactl info | grep Sink

Skal vise bluez_sink... som aktiv kanal

Høyttaleren kobles automatisk til neste gang ved oppstart

5. Visning i webpanelet og foreldreversjon

Denne hjelpen vises som egen knapp i webpanelet under navnet "Bruksanvisning".

Du kan skrive den ut fra nettleseren direkte (Ctrl+P eller Del → Skriv ut)

Du kan også laste ned PDF-versjonen:

Last ned PDF

For videre hjelp, kontakt systemansvarlig eller se prosjektets GitHub-repo.

# RFIDMusicBox
MusicBox med RFID styring
