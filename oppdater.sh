#!/bin/bash

echo "🔄 Henter siste endringer fra GitHub..."
cd /home/magic/programmer/RFIDMusicBox || exit 1
git pull

echo "🚀 Restarter tjenester..."
sudo systemctl restart rfid_webpanel.service
sudo systemctl restart rfid_trigger_listener.service