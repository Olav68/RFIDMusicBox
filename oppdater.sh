#!/bin/bash
# oppdater.sh – Henter nyeste versjon og restarter nødvendige tjenester

set -e  # Avslutt på første feil

echo "🔄 Oppdaterer RFIDMusicBox fra GitHub..."
cd /home/magic/RFIDMusicBox || { echo "❌ Katalog ikke funnet"; exit 1; }
git pull

echo "🚀 Starter tjenester på nytt..."
for service in rfid_webpanel.service rfid_trigger_listener.service rfid_input_listener.service; do
    echo "🔁 Restarter $service..."
    sudo systemctl restart "$service"
    echo "📋 Status for $service:"
    sudo systemctl status "$service" --no-pager --lines=5
done