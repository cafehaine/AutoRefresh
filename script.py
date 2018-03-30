#!/bin/python3

import pyinotify
import socket
from webbrowser import open as webopen
# used to treat request arguments
import re
from websocketmanager import websocketmanager
from httpmanager import handlehttp

HOST = "0.0.0.0"
BASEPORT = 8000

WEBSOCKETS = []


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


LANIP = getLanIp()

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
        # conn.settimeout(1)
        try:
            with conn:
                #------------------------------------#
                # Receive header and fetch arguments #
                #------------------------------------#

                print("Connected by", addr)
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
                print("\t" + method + " " + path)

                #---------------#
                # Treat request #
                #---------------#

                # WebSocket
                if path == "/__websocket":
                    websock = websocketmanager(conn, arguments)
                    WEBSOCKETS.append(websock)
                # File/Directory
                else:
                    handlehttp(conn, path)
            print("done")
        except socket.timeout:
            print("timeout")
