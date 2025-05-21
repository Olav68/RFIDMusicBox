#!/bin/bash

TAG="RFIDMusicBox"

# Finn status på wlan0
IFSTATE=$(cat /sys/class/net/wlan0/operstate 2>/dev/null)

if [ -z "$IFSTATE" ]; then
    logger -t "$TAG" "Fant ikke grensesnitt wlan0 – finnes det?"
    exit 1
fi

logger -t "$TAG" "Status for wlan0: $IFSTATE"

if [ "$IFSTATE" = "down" ]; then
    logger -t "$TAG" "wlan0 er nede – forsøker å sette opp"
    ip link set wlan0 up
    sleep 2
    NEWSTATE=$(cat /sys/class/net/wlan0/operstate)
    logger -t "$TAG" "Ny status etter 'ip link set': $NEWSTATE"
else
    logger -t "$TAG" "wlan0 er oppe – ingen tiltak"
fi