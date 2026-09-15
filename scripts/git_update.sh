#!/bin/bash
# Henter siste kode fra git hvis det finnes noe nytt. Brukes både av
# rfid_auto_update.service (ved oppstart) og av "Sjekk etter oppdatering"
# i webpanelet. Skal ALDRI blokkere/feile hardt - git-kall er tidsbegrenset
# slik at manglende nett ikke stopper resten av oppstarten.
REPO_DIR="/home/magic/programmer/RFIDMusicBox"
TIMEOUT=15

cd "$REPO_DIR" || exit 0

echo "🔄 Sjekker etter oppdatert kode..."
if ! timeout "$TIMEOUT" git fetch origin main; then
    echo "⚠️ Klarte ikke sjekke etter oppdateringer (ingen nett?) - fortsetter med nåværende versjon"
    exit 0
fi

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ Allerede på nyeste versjon ($LOCAL)"
    exit 0
fi

echo "⬇️ Ny versjon funnet ($LOCAL -> $REMOTE), oppdaterer..."
git reset --hard origin/main
# --break-system-packages: Raspberry Pi OS Bookworm nekter system-wide pip-installer
# ellers (PEP 668) - tjenestene kjører direkte mot /usr/bin/python3, ikke et venv.
timeout "$TIMEOUT" pip install -r requirements.txt --break-system-packages --quiet 2>/dev/null
echo "✅ Oppdatert til $(git rev-parse HEAD)"
echo "UPDATED"
