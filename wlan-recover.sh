# Sjekk status på wlan0
# Hvis wlan0 er nede, sett den opp
# Hvis wlan0 er oppe, gjør ingenting
IFSTATE=$(cat /sys/class/net/wlan0/operstate)

if [ "$IFSTATE" = "down" ]; then
    logger "RFIDMusicBox: wlan0 var nede – setter opp"
    ip link set wlan0 up
else
    logger "RFIDMusicBox: wlan0 er allerede oppe – ingen handling"
fi