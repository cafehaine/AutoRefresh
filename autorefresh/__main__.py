#!/bin/python3

from argparse import ArgumentParser, Namespace
import logging
import os
import re
import socket
import sys
from urllib.parse import quote
from webbrowser import open as webopen

import pyinotify

from autorefresh.httpmanager import HttpManager
from autorefresh import websocketmanager

BASEPORT = 8000


def get_lan_ip():
    """
    Return the LAN IPV4 address for this computer.

    Taken from https://stackoverflow.com/a/28950776/2279323
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("10.255.255.255", 1))
        inet = sock.getsockname()[0]
    except Exception:
        inet = "127.0.0.1"
    finally:
        sock.close()
    return inet


class EventHandler(pyinotify.ProcessEvent):
    """Inotify event handler."""

    def __init__(self, root):
        self.root = root

    def update(self, event):
        path = event.pathname[len(self.root) + 1 :]
        websocketmanager.update(quote(path))

    def process_IN_MODIFY(self, event):
        self.update(event)

    def process_IN_CREATE(self, event):
        self.update(event)

    def process_IN_DELETE(self, event):
        self.update(event)


def listen_loop(sock, notifier, http_manager):
    """Main server loop."""
    sock.listen()
    while True:
        try:
            conn, addr = sock.accept()
        except KeyboardInterrupt:
            print("Exiting...")
            notifier.stop()
            sys.exit(0)
        try:
            conn.settimeout(0.1)
            # ------------------------------------#
            # Receive header and fetch arguments #
            # ------------------------------------#

            logging.info("Connected by %s", addr)
            request = ""
            while True:
                data = conn.recv(1024)
                request = request + data.decode("utf-8")
                if request.endswith("\r\n\r\n"):
                    break
            lines = request.splitlines()
            # put arguments in a dict
            arguments = {}
            for line in lines:
                match = re.match(r"^(.*):\ (.*)$", line)
                if match is not None:
                    key, value = match.group(1, 2)
                    arguments[key] = value

            method, path, _ = lines[0].split(" ")
            logging.info("\t%s %s", method, path)

            # ---------------#
            # Treat request #
            # ---------------#

            # WebSocket
            if path == "/__websocket":
                conn.settimeout(5)
                websocketmanager.WebsocketSession(conn, arguments)
            # File/Directory
            else:
                conn.settimeout(5)
                http_manager.handlehttp(conn, path)
                conn.close()
            logging.info("done")
        except socket.timeout:
            logging.error("Socket from IP %s timed-out.", addr)


def main(namespace: Namespace) -> None:
    """Main function: setup the server and run it."""
    listen_address = "127.0.0.1" if namespace.local else "0.0.0.0"
    lan_ip = get_lan_ip()
    baseport = namespace.baseport
    root = namespace.root

    # Setup the watchdog
    watchdog = pyinotify.WatchManager()
    mask = pyinotify.IN_MODIFY | pyinotify.IN_CREATE | pyinotify.IN_DELETE

    notifier = pyinotify.ThreadedNotifier(watchdog, EventHandler(root))
    notifier.start()

    watchdog.add_watch(root, mask, rec=True)

    # Setup the server
    http_manager = HttpManager(root)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        bound = False
        while not bound:
            try:
                sock.bind((listen_address, baseport))
                bound = True
            except Exception:
                baseport += 1

        print(f"Connect to http://{lan_ip}:{baseport}")
        webopen(f"http://{lan_ip}:{baseport}")

        listen_loop(sock, notifier, http_manager)


if __name__ == "__main__":
    # Parse arguments
    parser = ArgumentParser()
    parser.add_argument(
        "-l",
        "--local",
        default=False,
        action="store_true",
        help="Only listen for connections from localhost.",
    )
    parser.add_argument("--baseport", default=BASEPORT, type=int, help="Starting port.")
    parser.add_argument(
        "root", default=os.getcwd(), type=str, nargs="?", help="The directory to serve."
    )

    main(parser.parse_args())
