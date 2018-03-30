#!/bin/python3

import pyinotify
import socket
import os
from webbrowser import open as webopen
import mimetypes
import sys
# used to treat request arguments
import re
from websocketmanager import websocketmanager

mimetypes.init()
PATH = os.path.realpath(os.path.dirname(sys.argv[0]))
CWD = os.getcwd()
HOST = "0.0.0.0"
BASEPORT = 8000

HTML_BEFORE = """<!DOCTYPE HTML>
<html>
 <head>
  <meta charset="utf8">
  <title>RefresHTML</title>
 </head>
 <body>"""

HTML_AFTER = """ </body>
</html>"""

WEBSOCKETS = []

# Javascript to be included at the end of each html documents
_js_source = open(PATH + "/included.js", "r")
JAVASCRIPT = "<script>" + _js_source.read() + "</script>"
_js_source.close()


def generateDirPage(path):
    ls = os.scandir(CWD + path)
    entries = []
    for entry in ls:
        entries.append(entry.name if entry.is_file() else (entry.name + "/"))
    ls.close()

    data = HTML_BEFORE
    data += "<h1>" + path + "</h1>"
    data += "<a href=\"../\">../</a><br>"
    for entry in entries:
        data += "<a href=\"" + entry + "\">" + entry + "</a><br>"
    data += HTML_AFTER
    return data


def getMimetype(path):
    val = "text/plain"
    try:
        val = mimetypes.types_map[os.path.splitext(path)[1]]
    except:
        pass
    return val


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
                elif os.path.exists(CWD + path):
                    conn.send(b"HTTP/1.0 200 OK\r\n")
                    # Directory
                    if path.endswith("/"):
                        conn.send(
                            ("Content-Type: " + mimetypes.types_map[".html"] +
                             "\r\n\r\n").encode())
                        data = generateDirPage(path)
                        conn.send(data.encode())
                    # File
                    else:
                        mime = getMimetype(path)
                        # HTML -> insert custom JS
                        if mime == "text/html":
                            data = open(CWD + path, mode="r")
                            content = data.read()
                            data.close()
                            content = content.replace("</body>",
                                                      JAVASCRIPT + "</body>")
                            conn.send((
                                "Content-Type: " + mime + "\r\n\r\n").encode())
                            conn.send(content.encode())
                        # Send file as-is
                        else:
                            data = open(CWD + path, mode="rb")
                            conn.send((
                                "Content-Type: " + mime + "\r\n\r\n").encode())
                            conn.send(data.read())
                            data.close()
                    conn.close()
                # 404
                else:
                    conn.send(b"HTTP/1.0 404 OK\r\n")
                    conn.send(b"Content-Type: text/plain\r\n\r\n")
                    conn.send(b"err 404")
                    conn.close()
            print("done")
        except socket.timeout:
            print("timeout")
