import hashlib
from base64 import b64encode


class websocketmanager:
    def __init__(self, socket, arguments):
        self.sock = socket
        socket.send(b"HTTP/1.1 101 Switching Protocols\r\n")
        socket.send(b"Upgrade: websocket\r\n")
        socket.send(b"Connection: Upgrade\r\n")
        keyhash = b64encode(
            hashlib.sha1(arguments["Sec-WebSocket-Key"].encode() +
                         b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11").digest())
        socket.send(b"Sec-WebSocket-Accept: " + keyhash + b"\r\n")
        socket.send(b"Sec-WebSocket-Protocol: chat\r\n\r\n")
        data = socket.recv(1024)
        print(data)
