#!/bin/python3

import logging
import os
import re
import socket
import sys
from urllib.parse import quote
from webbrowser import open as webopen

import pyinotify

from autorefresh.httpmanager import handlehttp
from autorefresh import websocketmanager

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
mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE  # watched events


class EventHandler(pyinotify.ProcessEvent):
    def update(self, event):
        path = event.pathname[len(CWD)+1:]
        websocketmanager.update(quote(path))

    def process_IN_MODIFY(self, event):
        self.update(event)

    def process_IN_CREATE(self, event):
        self.update(event)

    def process_IN_DELETE(self, event):
        self.update(event)


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
        try:
            conn, addr = s.accept()
        except KeyboardInterrupt:
            print("Exiting...")
            notifier.stop()
            sys.exit(0)
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
