#!/usr/bin/env bash

# Install system dependencies
sudo apt-get update -y
sudo apt-get install python3 can-utils xterm -y --no-install-recommends

# Install Python dependencies
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt

# Get the Zenite Solar's CAN_IDS protocol description file
wget https://raw.githubusercontent.com/ZeniteSolar/CAN_IDS/master/can_ids.json -O can_ids.json

# Generate the Simple Can Monitor service file
SERVICE_FILE=$PWD/simple_can_monitor.service
cat << EOF > $SERVICE_FILE
[Unit]
Description=Simple Can Monitor
After=graphical.target

[Service]
ExecStart=$PWD/run.sh
WorkingDirectory=$PWD
User=joaoantoniocardoso
Environment=SPAWN_WINDOW=1
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
EOF
echo "Service file '$SERVICE_FILE' generated."

# Install the systemd service
sudo systemctl link $SERVICE_FILE
sudo systemctl daemon-reload
sudo systemctl enable simple_can_monitor.service
