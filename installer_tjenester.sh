#!/bin/bash

echo "📦 Henter og installerer RFIDMusicBox-tjenester..."

REPO_DIR="/home/magic/programmer/RFIDMusicBox"
SERVICE_DIR="$REPO_DIR/services"
USER_NAME="magic"
USER_ID=$(id -u "$USER_NAME")

# Gå til prosjektmappen og hent siste fra Git
if [ -d "$REPO_DIR/.git" ]; then
  echo "🔄 Tilbakestiller lokale endringer og henter fra GitHub..."
  cd "$REPO_DIR" || exit 1
  git reset --hard || exit 1
  git pull || exit 1
else
  echo "❌ Git-repo ikke funnet i $REPO_DIR"
  exit 1
fi

# Sjekk at service-mappen finnes
if [ ! -d "$SERVICE_DIR" ]; then
  echo "❌ Fant ikke service-mappen: $SERVICE_DIR"
  exit 1
fi

# Stopper og deaktiverer gamle tjenester
echo "🧹 Stopper gamle tjenester (hvis de kjører)..."
for SERVICE in rfid_webpanel rfid_trigger_listener rfid_input_listener; do
  sudo systemctl stop "$SERVICE" 2>/dev/null
  sudo systemctl disable "$SERVICE" 2>/dev/null
done

# Kopier tjenestefiler
echo "📝 Kopierer tjenester til /etc/systemd/system/"
sudo cp "$SERVICE_DIR"/rfid_*.service /etc/systemd/system/

# Legg til manglende Environment-linjer hvis de mangler
for FILE in /etc/systemd/system/rfid_*.service; do
  if ! grep -q "XDG_RUNTIME_DIR" "$FILE"; then
    sudo sed -i "/^User=$USER_NAME/a Environment=XDG_RUNTIME_DIR=/run/user/$USER_ID" "$FILE"
  fi
done

# Last systemd på nytt
echo "🔁 Laster systemd daemon på nytt..."
sudo systemctl daemon-reexec
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