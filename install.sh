#!/bin/bash
set -eux
sudo install buttond irc-topic-changer.py /usr/local/bin/
sudo install -m 644 *.service /etc/systemd/system/
