#!/usr/bin/env python3
# IRC client code derived from work by Pepijn de Vos
# https://badge.sha2017.org/projects/irc_pager

import socket
import re
import threading
import subprocess
from subprocess import Popen, PIPE

ENCODING = "UTF-8"
EOL = "\r\n"
HOST = "chat.freenode.net"
#HOST = "127.0.0.1"
PORT = 6667

NICK = "hackeriet-button"
REALNAME = "space-status-button"
CHANNEL = "#oslohackerspace"

s = socket.socket()
s.connect((HOST, PORT))

f = s.makefile(mode='r', encoding=ENCODING, newline=EOL)

def sendline(line):
  return s.send(bytes("%s%s" % (line, EOL), ENCODING))

def readline():
  return f.readline().rstrip()

def changetopic(status):
  # Avoid setting an empty topic on start
  if len(topic) > 0:
    # The existing topic is expected to contain "space is: <topic> |"
    new_topic = re.sub(r"(space is: )([^\|]+)", r"\1%s " % status, topic)
    sendline("TOPIC %s :%s" % (CHANNEL, new_topic))

sendline("NICK %s" % NICK)
sendline("USER %s 0 * :%s" % (NICK, REALNAME))
sendline("JOIN %s" % CHANNEL)

# TODO: read the topic on start and subsequent topic changes
#       or read the topic before changing it each time

def journal_reader():
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

    # TODO: logger.verbose
    print("** " + re.sub(r"[\r\n]+", "", line))

# Read the journal on a separate thread to determine if the button
# has been pressed.
t = threading.Thread(name='child procs', target=journal_reader)
t.start()

topic = ''

# Handle IRC connection and its events
while 1:
  line = readline()
  parts = line.split()

  if parts:
    # Perform the most important IRC task
    if parts[0] == "PING":
      sendline("PONG %s" % line[1])

    # Save advertised topic on join
    if parts[1] == "332":
      topic = ' '.join(parts[4:])[1:]
      print("** Initial topic saved to cache: %s" % topic)

    # Save updated updated topics
    if parts[1] == "TOPIC":
      topic = ' '.join(parts[3:])[1:]
      # TODO: logger.<?>
      print("** New topic saved to cache: %s" % topic)

    # TODO: logger.debug
    print(line)

