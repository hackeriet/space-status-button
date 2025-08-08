# space-status-button

Software for a button to set the entrance status

Expected to run on a Raspberry Pi

## `buttond`
A program to watch changes on a GPIO pin
  - Depends on `mosquitto-clients` to publish messages to an MQTT broker

## `irc-topic-changer.py`
An IRC client daemon
  - Depends on `python` >= 3.5.3
  - Reads the output of `buttond` by reading the systemd journal
  - Changes topic in an IRC channel when button status changes
  - Relies on systemd to restart the IRC daemon on errors
