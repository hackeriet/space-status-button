#!/usr/bin/env python3
# IRC client code derived from work by Pepijn de Vos
# https://badge.sha2017.org/projects/irc_pager

import socket
import ssl
import re
import threading
import logging
import time
import os
from sys import exit
from subprocess import Popen, PIPE


ENCODING = "UTF-8"
EOL = "\r\n"
HOST = "irc.libera.chat"
#HOST = "127.0.0.1"
PORT = 6697
IRC_NICK = os.getenv("IRC_NICK", default="hackeriet-button")
IRC_PASS = os.getenv("IRC_PASS", default=0)
IRC_CHANNEL = os.getenv("IRC_CHANNEL", default="#oslohackerspace")
REALNAME = "space-status-button"
DEBUG = bool(os.getenv("DEBUG", default="0"))

logging.basicConfig(level=logging.DEBUG if DEBUG else logging.INFO)

#ctx = ssl.create_default_context(purpose=ssl.Purpose.CLIENT_AUTH)
ctx = ssl.create_default_context(purpose=ssl.Purpose.SERVER_AUTH)
sock = socket.socket()
s = ctx.wrap_socket(sock, server_hostname="irc.libera.chat")
s.connect((HOST, PORT))

f = s.makefile(mode='r', encoding=ENCODING, newline=EOL)

def sendline(line):
    """Sends a string line to the socket"""
    logging.info("Sending line: %s", line)
    return s.send(bytes("%s%s" % (line, EOL), ENCODING))

def changetopic(status):
    # Avoid setting an empty topic on start
    if len(topic) > 0:
        # The existing topic is expected to contain "space is: <topic> |"
        new_topic = re.sub(r"(space is: )([^\|]+)", r"\1%s " % status, topic)
        sendline("PRIVMSG ChanServ :TOPIC %s %s" % (IRC_CHANNEL, new_topic))

logging.debug("Pass: %s" % IRC_PASS)
sendline("NICK %s" % IRC_NICK)
sendline("USER %s %s * :%s" % (IRC_NICK, IRC_PASS, REALNAME))
sendline("PRIVMSG NickServ :IDENTIFY %s" % IRC_PASS)
sendline("JOIN %s" % IRC_CHANNEL)

def journal_reader():
    """
    Reads the systemd journal for button events and calls changetopic
    """
    proc = Popen(["journalctl", "-f", "-u", "buttond"], stdout=PIPE, bufsize=1)
    for line in iter(proc.stdout.readline, b''):
        line = line.decode('utf-8')
        search = re.search(r"Button state set to (0|1)", line)
        if search is not None:
            button_state = search.group(1)
            if button_state == '1':
                changetopic("OPEN")
            else:
                changetopic("CLOSED")

        logging.debug(re.sub(r"[\r\n]+", "", line))

# Read the journal on a separate thread to determine if the button
# has been pressed.
t = threading.Thread(name='child procs', target=journal_reader, daemon=True)
t.start()

def pinger():
    """
    Pings a system user on the network periodically to detect loss of connectivity
    """
    while True:
        time.sleep(120)
        logging.debug("pinging server")
        sendline("PING ChanServ")

pinger_t = threading.Thread(target=pinger, daemon=True)
pinger_t.start()

topic = ''

# Handle IRC connection and its events
while 1:
    try:
        line = f.readline().rstrip()
    except UnicodeDecodeError as e:
        logging.error("Failed to decode; ignoring line.")
        logging.error(e)
        continue

    # Reading an empty line signifies a dead connection
    if not line:
        logging.error("Exiting (socket closed)")
        exit(1)

    parts = line.split()

    if parts:
        logging.debug(line)

        # Perform the most important IRC task
        if parts[0] == "PING":
            sendline("PONG %s" % parts[1])

        # Save advertised topic on join
        if parts[1] == "332":
            topic = ' '.join(parts[4:])[1:]
            logging.info("Initial topic saved to cache: %s", topic)

        # Nickname already taken
        if parts[1] == "433":
            logging.error("Exiting (nickname already taken)")
            exit(1)

        # Save updated updated topics
        if parts[1] == "TOPIC":
            topic = ' '.join(parts[3:])[1:]
            logging.info("New topic saved to cache: %s", topic)
