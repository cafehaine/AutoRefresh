#!/bin/python3

import pyinotify
import socket
import os
import mimetypes

mimetypes.init()
PATH = os.getcwd()
HOST = '127.0.0.1'
PORT = 8000

HTML_BEFORE = """<!DOCTYPE HTML>
<html>
 <head>
  <meta charset="utf8">
  <title>RefresHTML</title>
 </head>
 <body>"""

HTML_AFTER = """ </body>
</html>"""


def generateDirPage(path):
    ls = os.scandir(PATH + path)
    entries = []
    for entry in ls:
        entries.append(entry.name if entry.is_file() else (entry.name + "/"))
    ls.close()

    data = HTML_BEFORE
    data += "<h1>"+path+"</h1>"
    data += "<a href=\"../\">../</a><br>"
    for entry in entries:
        data += "<a href=\"" + entry + "\">" + entry + "</a><br>"
    data += HTML_AFTER
    return data

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    binded = False
    while not binded:
        try:
            s.bind((HOST, PORT))
            binded = True
        except Exception:
            PORT+=1

    print("Listening on http://127.0.0.1:" + str(PORT))
    s.listen(1)
    while True:
        conn, addr = s.accept()
        conn.settimeout(1)
        try:
            with conn:
                print('Connected by', addr)
                request = ""
                while True:
                    data = conn.recv(1024)
                    request = request + data.decode("utf-8")
                    if request.endswith("\r\n\r\n"): break
                lines = request.splitlines()
                method, path, protocol = lines[0].split(" ")
                print("\t" + method + " " + path)
                conn.send('HTTP/1.0 200 OK\r\n'.encode())
                if path.endswith("/"):
                    conn.send(("Content-Type: " + mimetypes.types_map[".html"] + "\r\n\r\n").encode())
                    data = generateDirPage(path)
                    conn.send(data.encode())
                else:
                    data = open(PATH + path, mode="rb")
                    conn.send(("Content-Type: " + mimetypes.types_map[os.path.splitext(path)[1]] + "\r\n\r\n").encode())
                    l = data.read(1024)
                    while (l):
                        conn.send(l)
                        l = data.read(1024)
                conn.close()
        except socket.timeout:
            print("timeout")
