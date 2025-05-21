#!/bin/bash

echo "📦 Henter og installerer RFIDMusicBox-tjenester..."

REPO_DIR="/home/magic/programmer/RFIDMusicBox"
SERVICE_DIR="$REPO_DIR/services"

# Gå til prosjektmappen og hent siste fra Git
if [ -d "$REPO_DIR/.git" ]; then
  echo "🔄 Tilbakestiller lokale endringer og henter fra GitHub..."
  cd "$REPO_DIR" || exit 1
  git reset --hard
  git pull
else
  echo "❌ Git-repo ikke funnet i $REPO_DIR"
  exit 1
fi

# Sjekk at service-mappen finnes
if [ ! -d "$SERVICE_DIR" ]; then
  echo "❌ Fant ikke service-mappen: $SERVICE_DIR"
  exit 1
fi

# Kopier tjenestefiler
echo "📝 Kopierer tjenester til /etc/systemd/system/"
sudo cp "$SERVICE_DIR"/rfid_*.service /etc/systemd/system/

# Last systemd på nytt
echo "🔁 Laster systemd daemon på nytt..."
sudo systemctl daemon-reload

# Aktiver og start tjenestene
for SERVICE in rfid_webpanel rfid_trigger_listener rfid_input_listener; do
  if [ -f "/etc/systemd/system/${SERVICE}.service" ]; then
    echo "✅ Aktiverer og restarter $SERVICE"
    sudo systemctl enable "$SERVICE"
    sudo systemctl restart "$SERVICE"
    sudo systemctl status "$SERVICE" --no-pager
  else
    echo "⚠️ Tjenestefil mangler: ${SERVICE}.service"
  fi
done

echo "🎉 Installasjon og oppdatering fullført!"