#!/usr/bin/env sh

CAN_DEVICE=can0

sudo ip link add dev $CAN_DEVICE
sudo ip link set up dev $CAN_DEVICE

python main.py
