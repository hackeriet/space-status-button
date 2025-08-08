#!/bin/bash
set -eux
sudo useradd -d $(pwd) button || true
sudo usermod -a -G gpio button
sudo usermod -a -G systemd-journal button
sudo apt install -y mosquitto-clients
sudo install buttond irc-topic-changer.py /usr/local/bin/
sudo install -m 644 *.service /etc/systemd/system/
