from helpers import get_port, MySocket
import errno
import shelve
from hashlib import pbkdf2_hmac
import secrets
from base64 import b64encode
from threading import Thread, Event


class Server:
    def __init__(self):
        self.sock = MySocket()
        self.auth_conns = set()

        try:
            self.sock.bind(('', get_port()))
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                print('port is not available, using a free port')
                self.sock.bind(('', 0))
            else:
                raise e
        self.log('server started')

        self.sock.listen()
        print(f'listening on port {self.sock.getsockname()[1]}')

        self.passwords_db = shelve.open('passwords')
        self.session_tokens_db = shelve.open('session_tokens')

    def log(self, *values):
        with open('server.log', 'a') as f:
            print(*values, file=f)

    def authenticate(self, conn) -> bool:
        def greet(name):
            return b'hello ' + name.encode() + b'\n'

        conn.sendall(b'session token (blank if none): ')
        session_token = conn.recv()
        if session_token:
            session_token = session_token.decode()
            for st, n in self.session_tokens_db.items():
                if session_token == st:
                    name = n
                    self.log('authenticated using session token')
                    conn.sendall(greet(name))
                    return name
            conn.sendall(b'wrong session token!\n')
            self.log('got wrong session token')
        else:
            conn.sendall(b'username: ')
            name = conn.recv().decode()
            conn.sendall(b'password: ')
            password = conn.recv()
            salt_and_hash = self.passwords_db.get(name)
            if salt_and_hash is None:
                salt = secrets.token_bytes(512 // 8)
                hash = pbkdf2_hmac('sha256', password, salt, 100_000)
                self.passwords_db[name] = (salt, hash)
                session_token = b64encode(secrets.token_bytes())
                self.session_tokens_db[session_token.decode()] = name
                self.log('registered user')
                conn.sendall(greet(name) +
                             b'your session token is ' + session_token + b'\n')
                return name
            else:
                (salt, hash) = salt_and_hash
                if pbkdf2_hmac('sha256', password, salt, 100_000) == hash:
                    self.log('authenticated using password')
                    session_token = b64encode(secrets.token_bytes())
                    self.session_tokens_db[session_token.decode()] = name
                    conn.sendall(greet(name) + b'your new session token is '
                                 + session_token + b'\n')
                    return name
                else:
                    conn.sendall(b'wrong password!\n')
                    self.log('got wrong password')

    def handle_connection(self, conn, addr):
        name = self.authenticate(conn)
        if not name:
            return

        self.auth_conns.add(conn)
        conn.settimeout(1)

        while not self.exit_event.is_set():
            self.pause_event.wait()
            try:
                msg = conn.recv()
            except TimeoutError:
                continue
            if msg is None:
                self.log(f'disconnected {addr}')
                self.auth_conns.remove(conn)
                break
            self.log(f'received {len(msg)} bytes')

            for user in self.auth_conns:
                if user is not conn:
                    user.sendall(name.encode() + b': ' + msg + b'\n')

    def accept_loop(self):
        self.exit_event = Event()
        self.pause_event = Event()
        self.pause_event.set()
        self.sock.settimeout(1)
        while not self.exit_event.is_set():
            self.pause_event.wait()
            try:
                conn, addr = self.sock.accept()
            except TimeoutError:
                continue
            self.log(f'connected client {addr}')
            Thread(target=self.handle_connection, args=[conn, addr]).start()

    def input_loop(self):
        while True:
            command = input('> ')
            if command == 'exit':
                self.exit_event.set()
                return
            elif command == 'pause':
                self.pause_event.clear()
            elif command == 'unpause':
                self.pause_event.set()
            elif command == 'show-logs':
                with open('server.log') as f:
                    print(f.read())
            elif command == 'clear-logs':
                open('server.log', 'w').close()
            elif command == 'clear-credentials':
                self.passwords_db.clear()
                self.session_tokens_db.clear()
            else:
                print('unknown command')


def main():
    server = Server()
    Thread(target=server.accept_loop).start()
    server.input_loop()


if __name__ == '__main__':
    main()
