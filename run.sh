#!/usr/bin/env bash

# CAN CONFIG
CAN_BITRATE=500000

# XTERM CONFIG
XTERM_BORDERWIDTH=0
XTERM_FONTSIZE=20
XTERM_FONT="Monospace"
XTERM_FONTCOLOR="white"
XTERM_BACKGROUNDCOLOR="black"

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
    xterm \
        -display :0 \
        -title "xterm: Simple Can Monitor" \
        +maximized \
        # -hold \
        -mesg \
        +fbx \
        -fa $XTERM_FONT \
        -fs $XTERM_FONTSIZE \
        -bw $XTERM_BORDERWIDTH \
        -bg $XTERM_BACKGROUNDCOLOR \
        -fg $XTERM_FONTCOLOR \
        -e "source .env/bin/activate && python3 main.py"
else
    echo "Starting in the current terminal..."
    source .env/bin/activate && \
    python3 main.py
fi
