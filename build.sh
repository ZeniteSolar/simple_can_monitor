#!/usr/bin/env bash

# Install system dependencies
sudo apt-get update -y
sudo apt-get install -y --no-install-recommends \
  python3 \
  can-utils \
  xterm \
  at-spi2-core \
  fonts-hack-ttf

# Reload fonts
fc-cache

# Increase user's permissions to use ip command
echo -e "\e[33mUNSAFE: Increasing user's permissions to use ip command...\e[0m"

# Ask the user if they want to continue
read -p "Do you want to continue? (y/n) " -n 1 -r
# Move to a new line
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
  echo -e "\e[32mIncreasing user's permissions to use ip command...\e[0m"
  sudo chmod u+s /bin/ip
else
    echo "Operation cancelled by user."
fi

# Install Python dependencies
python3 -m venv .env
source .env/bin/activate
python3 -m pip install -r requirements.txt

# Get the Zenite Solar's CAN_IDS protocol description file
wget https://raw.githubusercontent.com/ZeniteSolar/CAN_IDS/master/can_ids.json -O can_ids.json

# Generate the Simple Can Monitor service file
SERVICE_FILE=$PWD/simple_can_monitor.service
cat << EOF > $SERVICE_FILE
[Unit]
Description=Simple Can Monitor
After=default.target

[Service]
ExecStart=$PWD/run.sh
WorkingDirectory=$PWD
User=$USER
Environment="SPAWN_WINDOW=1"
Environment="DISPLAY=:0"
Restart=always
RestartSec=3

[Install]
WantedBy=default.target
EOF
echo "Service file '$SERVICE_FILE' generated."

# Install the systemd service
sudo systemctl link $SERVICE_FILE
sudo systemctl daemon-reload
sudo systemctl enable simple_can_monitor.service
