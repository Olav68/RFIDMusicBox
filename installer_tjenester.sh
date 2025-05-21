#!/bin/bash

echo "📦 Installerer RFIDMusicBox-tjenester..."

SERVICE_DIR="/home/magic/RFIDMusicBox/services"

if [ ! -d "$SERVICE_DIR" ]; then
  echo "❌ Fant ikke service-mappen: $SERVICE_DIR"
  exit 1
fi

# Kopier alle tjenestefiler
echo "📝 Kopierer tjenester til /etc/systemd/system/"
sudo cp $SERVICE_DIR/rfid_*.service /etc/systemd/system/

# Last inn systemd på nytt
echo "🔄 Laster inn systemd-konfig"
sudo systemctl daemon-reload

# Aktiver og start tjenestene
for SERVICE in rfid_webpanel rfid_trigger_listener rfid_input_listener; do
  if [ -f "/etc/systemd/system/${SERVICE}.service" ]; then
    echo "✅ Aktiverer og starter $SERVICE"
    sudo systemctl enable "$SERVICE"
    sudo systemctl restart "$SERVICE"
    sudo systemctl status "$SERVICE" --no-pager
  else
    echo "⚠️ Tjenestefil mangler: ${SERVICE}.service"
  fi
done

echo "🎉 Installasjon fullført."