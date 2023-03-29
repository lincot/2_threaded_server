import socket


class MySocket(socket.socket):
    __slots__ = ()

    def sendall(self, data: bytes):
        super().sendall('{:04}'.format(len(data)).encode() + data)

    def recv(self, bufsize: int = 1024) -> bytes:
        data = super().recv(bufsize)
        if not data:
            return None
        return data[4:]

    def accept(self):
        (sock, addr) = super().accept()
        sock.__class__ = MySocket
        return (sock, addr)


DEFAULT_PORT = 9090


def get_port() -> int:
    port = input(f'enter server port ({DEFAULT_PORT}): ')
    if not port:
        return DEFAULT_PORT
    else:
        return int(port)
