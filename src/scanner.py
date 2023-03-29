import socket
from threading import Thread
from tqdm import tqdm


def scan_port(host, port, open_ports):
    sock = socket.socket()
    try:
        sock.connect((host, port))
        open_ports.append(port)
    except ConnectionRefusedError:
        pass
    sock.close()


DEFAULT_HOST = '127.0.0.1'


if __name__ == '__main__':
    threads = []
    open_ports = []

    host = input(f'host({DEFAULT_HOST}): ')
    if not host:
        host = DEFAULT_HOST

    for port in tqdm(range(2**16)):
        threads.append(Thread(target=scan_port, args=[host, port, open_ports]))

    for thread in tqdm(threads):
        thread.start()

    for thread in threads:
        thread.join()

    for port in open_ports:
        print(f'port {port} is open')
