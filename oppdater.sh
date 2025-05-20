#!/bin/bash

echo "🔄 Oppdaterer RFIDMusicBox fra GitHub..."
cd /home/magic/RFIDMusicBox || exit 1
git pull

echo "🚀 Starter tjenester på nytt..."
sudo /bin/systemctl restart rfid_webpanel.service
sudo /bin/systemctl restart rfid_reader.service

echo "📋 Status for rfid_webpanel:"
sudo /bin/systemctl status rfid_webpanel.service --no-pager

echo "📋 Status for rfid_reader:"
sudo /bin/systemctl status rfid_reader.service --no-pager
