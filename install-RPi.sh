#!/bin/bash
# this needs to be run as root on the RPi

ln -sf $(pwd)/button-machine.service /etc/systemd/system/
systemctl enable button-machine
systemctl restart button-machine
