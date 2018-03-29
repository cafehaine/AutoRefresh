#!/bin/python3

import pyinotify
import socket
import os
from webbrowser import open as webopen
import mimetypes
import sys
# used to treat request arguments
import re
# used to generate key for websocket communication
import hashlib
from base64 import b64encode

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
        conn.settimeout(1)
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

                if path == "/__websocket":
                    conn.send(b"HTTP/1.1 101 Switching Protocols\r\n")
                    conn.send(b"Upgrade: websocket\r\n")
                    conn.send(b"Connection: Upgrade\r\n")
                    keyhash = b64encode(
                        hashlib.sha1(arguments["Sec-WebSocket-Key"].encode(
                        ) + b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
                    conn.send(b"Sec-WebSocket-Accept: " + keyhash + b"\r\n")
                    conn.send(b"Sec-WebSocket-Protocol: chat\r\n\r\n")
                elif os.path.exists(CWD + path):
                    conn.send(b"HTTP/1.0 200 OK\r\n")
                    if path.endswith("/"):
                        conn.send(
                            ("Content-Type: " + mimetypes.types_map[".html"] +
                             "\r\n\r\n").encode())
                        data = generateDirPage(path)
                        conn.send(data.encode())
                    else:
                        mime = getMimetype(path)
                        if mime == "text/html":
                            data = open(CWD + path, mode="r")
                            content = data.read()
                            data.close()
                            content = content.replace("</body>",
                                                      JAVASCRIPT + "</body>")
                            conn.send((
                                "Content-Type: " + mime + "\r\n\r\n").encode())
                            conn.send(content.encode())
                        else:
                            data = open(CWD + path, mode="rb")
                            conn.send((
                                "Content-Type: " + mime + "\r\n\r\n").encode())
                            conn.send(data.read())
                            data.close()
                    conn.close()
                else:  # File does not exist
                    conn.send(b"HTTP/1.0 404 OK\r\n")
                    conn.send(b"Content-Type: text/plain\r\n\r\n")
                    conn.send(b"err 404")
                    conn.close()
        except socket.timeout:
            print("timeout")
