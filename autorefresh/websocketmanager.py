'''
This is a basic implementation of the websocket protocol (RFC 6455)

Since I din't want to read pages of specifications, all of what you see here is
based on https://stackoverflow.com/a/8125509/2279323
'''

import hashlib
from base64 import b64encode
from fnmatch import fnmatch
import json
from typing import List

__objects__: List['WebsocketSession'] = []


def close_all():
    """Close the sockets of all the WebsocketSession objects."""
    for obj in __objects__:
        obj.sock.close()


def update(path):
    """Check if any of the WebsocketSession should send an update signal."""
    for obj in __objects__:
        for cont_path in obj.content:
            if cont_path.endswith("*"):
                if fnmatch(path, cont_path):
                    obj.update()
                    break
            elif cont_path == path:
                obj.update()
                break


def __decodeframe__(data):
    """Decode a websocket frame."""
    second_byte = data[1]
    length = second_byte & 127  # may not be the actual length in the two special cases
    index_first_mask = 2  # if not a special case
    if length == 126:  # if a special case, change index_first_mask
        index_first_mask = 4
    elif length == 127:  # ditto
        index_first_mask = 10

    masks = data[index_first_mask:
                 index_first_mask + 4]  # four bytes starting from index_first_mask
    index_first_data_byte = index_first_mask + 4  # four bytes further
    decoded = ""
    j = 0
    for i in range(index_first_data_byte, len(data)):
        decoded += chr(data[i] ^ masks[j % 4])
        j += 1

    return decoded


def __encodeframe__(data):
    """Encode a websocket frame."""
    message = data.encode()
    output = [129]

    if len(message) <= 125:
        output.append(len(message))
    elif len(message) >= 126 and len(message) <= 65535:
        output.append(126)
        output.append((len(message) >> 8) & 255)
        output.append((len(message)) & 255)
    else:
        output.append(127)
        output.append((len(message) >> 56) & 255)
        output.append((len(message) >> 48) & 255)
        output.append((len(message) >> 40) & 255)
        output.append((len(message) >> 32) & 255)
        output.append((len(message) >> 24) & 255)
        output.append((len(message) >> 16) & 255)
        output.append((len(message) >> 8) & 255)
        output.append((len(message)) & 255)

    return bytes(output) + message


class WebsocketSession:
    def __init__(self, socket, arguments):
        self.sock = socket

        # Handshake
        socket.send(b"HTTP/1.1 101 Switching Protocols\r\n")
        socket.send(b"Upgrade: websocket\r\n")
        socket.send(b"Connection: Upgrade\r\n")
        keyhash = b64encode(
            hashlib.sha1(arguments["Sec-WebSocket-Key"].encode() +
                         b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
        socket.send(b"Sec-WebSocket-Accept: " + keyhash + b"\r\n")
        socket.send(b"Sec-WebSocket-Protocol: chat\r\n\r\n")
        data = socket.recv(1024)
        self.content = json.loads(__decodeframe__(data))
        socket.settimeout(None)
        __objects__.append(self)

    def update(self):
        self.sock.send(__encodeframe__("reload"))
        self.sock.close()
        __objects__.remove(self)
