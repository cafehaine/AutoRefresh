#!/bin/python3

import os
import socket
from webbrowser import open as webopen
import logging
import sys
# Request arguments treating
import re
# Sockets handling
import websocketmanager
from httpmanager import handlehttp
# Filesystem notification
import pyinotify

HOST = "0.0.0.0"
BASEPORT = 8000
CWD = os.getcwd()

#------------------#
# Argument parsing #
#------------------#

for i in range(1,len(sys.argv)):
    arg = sys.argv[i]
    if arg == "-l":
        HOST = "127.0.0.1"

# Taken from https://stackoverflow.com/a/28950776/2279323
def getLanIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        IP = s.getsockname()[0]
    except:
        IP = "127.0.0.1"
    finally:
        s.close()
    return IP


LANIP = HOST if HOST == "127.0.0.1" else getLanIp()

#---------------#
# Inotify setup #
#---------------#

wm = pyinotify.WatchManager()  # Watch Manager
mask = pyinotify.IN_MODIFY  # watched events


class EventHandler(pyinotify.ProcessEvent):
    def process_IN_MODIFY(self, event):
        websocketmanager.update(event.pathname[len(CWD) + 1:])


notifier = pyinotify.ThreadedNotifier(wm, EventHandler())
notifier.start()

wdd = wm.add_watch(CWD, mask, rec=True)

#----------------#
# Server startup #
#----------------#

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    binded = False
    while not binded:
        try:
            s.bind((HOST, BASEPORT))
            binded = True
        except Exception:
            BASEPORT += 1

    print("Connect to http://" + LANIP + ":" + str(BASEPORT))
    webopen("http://" + LANIP + ":" + str(BASEPORT))
    s.listen(1)
    while True:
        conn, addr = s.accept()
        try:
            conn.settimeout(0.1)
            #------------------------------------#
            # Receive header and fetch arguments #
            #------------------------------------#

            logging.info("Connected by", addr)
            request = ""
            while True:
                data = conn.recv(1024)
                request = request + data.decode("utf-8")
                if request.endswith("\r\n\r\n"): break
            lines = request.splitlines()
            # put arguments in a dict
            arguments = {}
            for l in lines:
                match = re.match("^(.*):\ (.*)$", l)
                if match != None:
                    key, value = match.group(1, 2)
                    arguments[key] = value

            method, path, protocol = lines[0].split(" ")
            logging.info("\t" + method + " " + path)

            #---------------#
            # Treat request #
            #---------------#

            # WebSocket
            if path == "/__websocket":
                conn.settimeout(5)
                websock = websocketmanager.websocketmanager(conn, arguments)
            # File/Directory
            else:
                conn.settimeout(5)
                handlehttp(conn, path)
                conn.close()
            logging.info("done")
        except socket.timeout:
            logging.error("Socket from IP " + str(addr) + " timed-out.")
