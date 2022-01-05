import json
import socket
import traceback
from io import BytesIO
from typing import Generator, Iterator

import itertools


def get_sock():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


class Server:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.sock.bind(('', 0))
        self.sock.listen(1)

    @property
    def port(self):
        return self.sock.getsockname()[1]

    def recv_all(self):
        # adapted from https://stackoverflow.com/a/29024384/6744133
        conn, addr = self.sock.accept()
        while True:
            msg_len_bytes = conn.recv(4)
            if not msg_len_bytes:
                # connection closed
                return
            msg_len = int.from_bytes(msg_len_bytes, 'big', signed=False)
            with BytesIO() as buffer:
                received_len = 0
                while received_len < msg_len:
                    resp = conn.recv(min(msg_len - received_len, 512))
                    received_len += len(resp)
                    if not resp:
                        # connection closed
                        return
                    buffer.write(resp)
                yield json.loads(buffer.getvalue().decode())


class Client:
    def __init__(self, sock: socket.socket, port: int):
        self.sock = sock
        self.sock.connect(('localhost', port))

    def send(self, data):
        msg = json.dumps(data).encode()
        self.sock.sendall(len(msg).to_bytes(4, 'big', signed=False))
        self.sock.sendall(msg)

    def run(self, it: Iterator):
        sock_error = None
        try:
            for item in itertools.chain(it, ({'type': 'close'},)):
                try:
                    self.send(item)
                except OSError as e:
                    sock_error = e
        except Exception as e:
            tb = traceback.format_exc()
            self.send({'type': 'error', 'traceback': tb})
        else:
            if sock_error is not None:
                raise sock_error
