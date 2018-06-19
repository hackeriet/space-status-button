# space-status-button

Button for setting public space entrance status

- Consists of a button status daemon and an IRC client daemon
- Reads the output of button daemon via systemd journal
- Changes topic in IRC channel when button status changes
- Relies on systemd to restart the IRC daemon on errors
