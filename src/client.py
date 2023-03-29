from helpers import get_port, MySocket
from threading import Thread

DEFAULT_HOST = '127.0.0.1'


def get_host():
    host = input(f'enter server host ({DEFAULT_HOST}): ')
    if not host:
        return DEFAULT_HOST
    else:
        return host


def receive_loop(sock):
    while True:
        data = sock.recv()
        if data is None:
            return
        print(data.decode(), end='', flush=True)


def main():
    host = get_host()
    port = get_port()
    sock = MySocket()
    sock.setblocking(True)
    sock.connect((host, port))
    print(f'connected to {host}:{port}')
    t = Thread(target=receive_loop, args=[sock])
    t.start()
    while t.is_alive():
        sock.sendall(input().encode())


if __name__ == '__main__':
    main()
