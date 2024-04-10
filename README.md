# simple_can_monitor

This is a hacky tool to monitor the boat data during tests.

![image](https://github.com/ZeniteSolar/simple_can_monitor/assets/5920286/f31b1db8-f59a-497b-b1d9-38c033bd4b36)

Then, play some candump file:
```Bash
canplayer vcan0=can0 -I ~/ZeniteSolar/2023/can_data/01072023/datasets/can/candump/candump-2023-07-01_145823.log
```

# Setup the Pi on the first use

## Setup WIFI to automatically connect
Just follow: https://www.tech-sparks.com/raspberry-pi-auto-connect-to-wifi/

## Install dependencies
```bash
sudo apt update -y && \
sudo apt install -y --no-install-recommends git cpufrequtils
```

## Allow ssh -X (for debug/developing only)
```bash
echo '\nX11Forwarding yes' | sudo tee -a /etc/ssh/sshd_config
```

## Configure SPI/CAN
```bash
echo 'dtoverlay=mcp2515-can0,oscillator=16000000,interrupt=25' | sudo tee -a /boot/config.txt
sudo sed -i '/dtparam=spi=on/s/^#//g' /boot/config.txt
```

## Set CPU to performance mode
```bash
echo 'GOVERNOR="performance"' | sudo tee -a /etc/default/cpufrequtils
sudo systemctl restart cpufrequtils
```

## Disable monitor power-save
```bash
sudo sed -i 's/#xserver-command=X/xserver-command=X -s 0 -dpms/' /etc/lightdm/lightdm.conf
```

## Install our simple can monitor
```bash
git clone https://github.com/ZeniteSolar/simple_can_monitor
cd simple_can_monitor
./build.sh
```

# Using

To install and run it as a systemd service, run:
```Bash
build.sh
```

To uninstall it: 
```Bash
sudo systemctl disable simple_can_monitor.service
```

To stop it:
```Bash
sudo systemctl stop simple_can_monitor.service
```

# Developing

The Messages shown can be changed by directly changing the `main.py` code.

Add a virtual can interface:
```Bash
sudo ip link add dev vcan0 type vcan
```

To run the script on a given terminal, just call:
```Bash
run.sh
```
