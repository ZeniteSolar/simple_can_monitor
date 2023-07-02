#!/usr/bin/env sh

sudo apt-get update -y
sudo apt-get install python can-utils -y --no-install-recommends

pip install --user -r requirements.txt

wget https://raw.githubusercontent.com/ZeniteSolar/CAN_IDS/master/can_ids.json -O can_ids.json
