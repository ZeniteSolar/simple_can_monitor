# simple_can_monitor

This is a hacky tool to monitor the boat data during tests.

![image](https://github.com/ZeniteSolar/simple_can_monitor/assets/5920286/f31b1db8-f59a-497b-b1d9-38c033bd4b36)

## Using

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

## Developing

The Messages shown can be changed by directly changing the `main.py` code.

Add a virtual can interface:
```Bash
sudo ip link add dev vcan0 type vcan
```

To run the script on a given terminal, just call:
```Bash
run.sh
```

Then, play some candump file:
```Bash
canplayer vcan0=can0 -I ~/ZeniteSolar/2023/can_data/01072023/datasets/can/candump/candump-2023-07-01_145823.log
```
