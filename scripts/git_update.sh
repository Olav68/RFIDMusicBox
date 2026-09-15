#!/bin/bash
# Henter siste kode fra git og oppdaterer Python-avhengigheter. Brukes av
# rfid_auto_update.service ved oppstart (uten --full, for rask oppstart) og
# av "Oppdater app"-knappen i webpanelet (med --full, som i tillegg
# oppdaterer systempakker via apt). Skal ALDRI blokkere/feile hardt -
# nettverkskall er tidsbegrenset slik at manglende nett ikke stopper
# resten av oppstarten.
REPO_DIR="/home/magic/programmer/RFIDMusicBox"
GIT_TIMEOUT=15
PIP_TIMEOUT=30
APT_TIMEOUT=300

FULL=false
[ "$1" = "--full" ] && FULL=true

cd "$REPO_DIR" || exit 0

CHANGED=false

echo "🔄 Sjekker etter oppdatert kode..."
if ! timeout "$GIT_TIMEOUT" git fetch origin main; then
    echo "⚠️ Klarte ikke sjekke etter kodeoppdateringer (ingen nett?)"
else
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main)
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "⬇️ Ny versjon funnet ($LOCAL -> $REMOTE), oppdaterer..."
        git reset --hard origin/main
        CHANGED=true
    else
        echo "✅ Kode allerede på nyeste versjon ($LOCAL)"
    fi
fi

echo "🐍 Sjekker Python-avhengigheter..."
# --break-system-packages: Raspberry Pi OS Bookworm nekter system-wide pip-installer
# ellers (PEP 668) - tjenestene kjører direkte mot /usr/bin/python3, ikke et venv.
# --upgrade: fanger opp f.eks. nyere yt-dlp selv om appens egen kode ikke har endret seg -
# yt-dlp må oppdateres jevnlig for at YouTube-nedlasting skal fortsette å fungere.
PIP_OUT=$(timeout "$PIP_TIMEOUT" pip install --upgrade -r requirements.txt --break-system-packages --quiet 2>&1)
if echo "$PIP_OUT" | grep -q "Successfully installed"; then
    echo "✅ Python-avhengigheter oppdatert"
    CHANGED=true
else
    echo "✅ Python-avhengigheter allerede oppdatert"
fi

if $FULL; then
    echo "📦 Sjekker systempakker (apt)..."
    if timeout "$APT_TIMEOUT" sudo apt-get update -qq; then
        UPGRADE_OUT=$(timeout "$APT_TIMEOUT" sudo apt-get upgrade -y -qq \
            -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold 2>&1)
        UPGRADED_COUNT=$(echo "$UPGRADE_OUT" | grep -oE "^[0-9]+ upgraded" | grep -oE "^[0-9]+")
        if [ -n "$UPGRADED_COUNT" ] && [ "$UPGRADED_COUNT" -gt 0 ]; then
            echo "✅ $UPGRADED_COUNT systempakke(r) oppdatert"
            CHANGED=true
        else
            echo "✅ Systempakker allerede oppdatert"
        fi
    else
        echo "⚠️ Klarte ikke sjekke etter systempakke-oppdateringer (ingen nett?)"
    fi
fi

if $CHANGED; then
    echo "✅ Oppdatering fullført"
    echo "UPDATED"
else
    echo "✅ Alt er allerede oppdatert - ingen endringer"
fi
