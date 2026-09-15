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

# Installer/oppdater systempakker (idempotent - hopper over allerede installerte)
DEPS_FILE="$REPO_DIR/scripts/apt-dependencies.txt"
if [ -f "$DEPS_FILE" ]; then
  echo "📦 Installerer systemavhengigheter fra $DEPS_FILE..."
  sudo apt-get update -qq
  # shellcheck disable=SC2046
  sudo apt-get install -y $(grep -vE '^\s*#|^\s*$' "$DEPS_FILE")
else
  echo "⚠️ Fant ikke $DEPS_FILE - hopper over systemavhengigheter"
fi

# PipeWire (lyd) kjører som en systemd --user-tjeneste knyttet til brukerens
# innloggingsøkt. Uten "linger" stopper den så snart ingen er logget inn via
# SSH/konsoll - på en headless boks betyr det at pactl/lydenheter slutter å
# fungere etter hver omstart. Idempotent å kjøre på nytt.
echo "🔊 Aktiverer linger for $USER_NAME (holder PipeWire i live uten innlogget økt)..."
sudo loginctl enable-linger "$USER_NAME"

# Stopper og deaktiverer gamle tjenester
echo "🧹 Stopper gamle tjenester (hvis de kjører)..."
for SERVICE in rfid_webpanel rfid_trigger_listener rfid_input_listener rfid_wifi_watchdog rfid_button_listener rfid_auto_update; do
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
for SERVICE in rfid_webpanel rfid_trigger_listener rfid_input_listener rfid_wifi_watchdog rfid_button_listener rfid_auto_update; do
  if [ -f "/etc/systemd/system/${SERVICE}.service" ]; then
    echo "✅ Aktiverer og restarter $SERVICE"
    sudo systemctl enable "$SERVICE"
    sudo systemctl restart "$SERVICE"
    sudo systemctl status "$SERVICE" --no-pager
  else
    echo "⚠️ Tjenestefil mangler: ${SERVICE}.service"
  fi
done

# Gi $USER_NAME passordløs tilgang til nøyaktig "systemctl reboot" (restart etter
# oppdatering), "apt-get update"/"apt-get upgrade" (systempakke-oppdatering) og
# "apt-get install" (sikre at nye avhengigheter i scripts/apt-dependencies.txt blir
# installert på eksisterende enheter), slik at webpanelet kan gjøre dette selv - Flask
# kjører ikke-interaktivt og kan ikke skrive inn et sudo-passord. Ingen andre apt-
# underkommandoer (remove/purge) gis tilgang.
SYSTEMCTL_PATH=$(command -v systemctl)
APT_GET_PATH=$(command -v apt-get)
SUDOERS_FILE="/etc/sudoers.d/rfidmusicbox"
echo "🔐 Setter opp passordløs sudo-tilgang for $USER_NAME (systemctl reboot, apt-get update/upgrade/install)..."
{
    echo "$USER_NAME ALL=(ALL) NOPASSWD: $SYSTEMCTL_PATH reboot"
    echo "$USER_NAME ALL=(ALL) NOPASSWD: $APT_GET_PATH update"
    echo "$USER_NAME ALL=(ALL) NOPASSWD: $APT_GET_PATH upgrade *"
    echo "$USER_NAME ALL=(ALL) NOPASSWD: $APT_GET_PATH install *"
} | sudo tee "$SUDOERS_FILE" > /dev/null
sudo chmod 440 "$SUDOERS_FILE"
sudo visudo -c -f "$SUDOERS_FILE" || echo "⚠️ Advarsel: $SUDOERS_FILE besto ikke visudo-sjekken, fjern/rett den manuelt"

echo "🎉 Installasjon og oppdatering fullført!"