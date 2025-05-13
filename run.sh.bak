#!/usr/bin/env bash

# CAN CONFIG
CAN_BITRATE=500000

# XTERM CONFIG
XTERM_BORDERWIDTH=0
XTERM_BORDERCOLOR='red'
XTERM_FONTSIZE=34
XTERM_FONT='Hack:style=Regular'
XTERM_FONTCOLOR='white'
XTERM_BACKGROUNDCOLOR='black'

# Find the first available CAN interface
CAN_INTERFACE=$(ip link show type can | awk -F: '{print $2}' | awk '{$1=$1;print}' | head -n 1)

# If no CAN interface found, try vcan
if [[ -z $CAN_INTERFACE ]]; then
    # Find the first available vcan interface
    VCAN_INTERFACE=$(ip link show type vcan | awk -F: '{print $2}' | awk '{$1=$1;print}' | head -n 1)

    if [[ -z $VCAN_INTERFACE ]]; then
        echo "No CAN or vcan interface found."
        exit 1
    fi

    CAN_INTERFACE=$VCAN_INTERFACE
fi

# Set the can interface up if its down
if ip link show "$CAN_INTERFACE" | grep -q "state DOWN"; then
    echo "Interface $CAN_INTERFACE is down. Setting link to up..."
    ip link set "$CAN_INTERFACE" up type can bitrate $CAN_BITRATE
    echo "Link for $CAN_INTERFACE is now up."
else
    echo "Interface $CAN_INTERFACE is already up."
fi

if [ -n "$SPAWN_WINDOW" ]; then
    echo "Waiting for X11 on display: '$DISPLAY'..."
    while [ ! "$(xset -q)" ]; do
        sleep 1
    done

    echo "Starting in a new xterm window..."
    ~/can_parser_rs --period=25 &
    sleep 5
    chromium-browser --start-fullscreen --temp-profile --incognito --app  http://localhost:3000
else

    echo "Starting in the current terminal..."
    ~/can_parser_rs --verbose --period=25 &
    sleep 5
    chromium-browser --start-fullscreen --temp-profile --incognito --app  http://localhost:3000
fi
