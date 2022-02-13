import json
import socket
import traceback
from io import BytesIO
from typing import Iterator


def get_sock():
    return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


class ChannelClosedException(Exception):
    pass


class Channel:
    def __init__(self, sock: socket.socket):
        self.sock = sock

    def send(self, data):
        msg = json.dumps(data).encode()
        self.sock.sendall(len(msg).to_bytes(4, 'big', signed=False))
        self.sock.sendall(msg)

    def recv(self):
        msg_len_bytes = self.sock.recv(4)
        if not msg_len_bytes:
            # connection closed
            raise ChannelClosedException()
        msg_len = int.from_bytes(msg_len_bytes, 'big', signed=False)
        with BytesIO() as buffer:
            received_len = 0
            while received_len < msg_len:
                resp = self.sock.recv(min(msg_len - received_len, 512))
                received_len += len(resp)
                if not resp:
                    # connection closed
                    raise ChannelClosedException()
                buffer.write(resp)
            return json.loads(buffer.getvalue().decode())


class Server:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.sock.bind(('', 0))
        self.sock.listen(1)
        self.sock.settimeout(1)

    @property
    def port(self):
        return self.sock.getsockname()[1]

    def accept(self):
        conn, addr = self.sock.accept()
        return Channel(conn)

    def recv_all(self, channel=None):
        if channel is None:
            channel = self.accept()
        while True:
            try:
                yield channel.recv()
            except ChannelClosedException:
                return


class Client(Channel):
    def __init__(self, sock: socket.socket, port: int):
        super().__init__(sock)
        self.sock.connect(('localhost', port))

    def run(self, it: Iterator):
        try:
            for item in it:
                self.send(item)
        except OSError as e:
            raise e
        except Exception:
            tb = traceback.format_exc()
            self.send({'type': 'error', 'traceback': tb})
        list(it)  # exhaust the iterator to make sure it completes


CLOSE_WINDOW = {'type': 'close_window'}
