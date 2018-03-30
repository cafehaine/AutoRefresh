'''
This is a basic implementation of the websocket protocol (RFC 6455)

Since I din't want to read pages of specifications, all of what you see here is
based on https://stackoverflow.com/a/8125509/2279323
'''


import hashlib
from base64 import b64encode
import json

def __decodeframe__(data):
    secondByte = data[1]
    length = secondByte & 127 # may not be the actual length in the two special cases
    indexFirstMask = 2 # if not a special case
    if length == 126: # if a special case, change indexFirstMask
        indexFirstMask = 4
    elif length == 127: # ditto
        indexFirstMask = 10

    masks = data[indexFirstMask : indexFirstMask + 4] # four bytes starting from indexFirstMask
    indexFirstDataByte = indexFirstMask + 4 # four bytes further
    decoded = ""
    j = 0
    for i in range(indexFirstDataByte,len(data)):
        decoded += chr(data[i] ^ masks[j % 4])
        j += 1
    
    return decoded

class websocketmanager:
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
        print(self.content)

