#!/bin/bash
echo "🔄 Henter siste endringer fra GitHub..."
cd "$HOME/programmer/RFIDMusicBox" || exit 1
git reset --hard
git pull

echo "🚀 Restarter brukertjenester..."
for SERVICE in rfid_webpanel rfid_trigger_listener rfid_input_listener; do
  systemctl --user restart "$SERVICE"
  systemctl --user status "$SERVICE" --no-pager
done