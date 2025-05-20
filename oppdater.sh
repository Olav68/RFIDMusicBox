#!/bin/bash
# oppdater.sh
echo "🔄 Oppdaterer RFIDMusicBox fra GitHub..."
cd /home/magic/RFIDMusicBox || exit 1
git pull

echo "🚀 Starter tjenester på nytt..."
sudo /bin/systemctl restart rfid_webpanel.service
sudo /bin/systemctl restart rfid_trigger_listener.service

echo "📋 Status for rfid_webpanel:"
sudo /bin/systemctl status rfid_webpanel.service --no-pager

echo "📋 Status for rfid_trigger_listener:"
sudo /bin/systemctl status rfid_trigger_listener.service --no-pager