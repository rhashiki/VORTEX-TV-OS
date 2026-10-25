"""Socket-level cancellation, total lifetime, recovery and cache cleanup checks."""
from contextlib import contextmanager
from pathlib import Path
import selectors
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('javac') and shutil.which('java'), 'JDK needed')
class TransferLifecycleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.classes = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.classes.cleanup)
        subprocess.run(['javac', '-encoding', 'UTF-8', '-d', cls.classes.name,
                        str(ROOT / 'app/src/main/java/os/vortex/tv/LanApkServer.java'),
                        str(ROOT / 'tests/LanApkServerLifecycleHarness.java')],
                       check=True, capture_output=True, text=True, timeout=30)

    def line(self, process):
        with selectors.DefaultSelector() as ready:
            ready.register(process.stdout, selectors.EVENT_READ)
            self.assertTrue(ready.select(timeout=3), 'Harness response timed out')
            line = process.stdout.readline().strip()
        self.assertTrue(line, 'Harness exited without response')
        return line

    def command(self, process, command):
        process.stdin.write(command + '\n')
        process.stdin.flush()
        return self.line(process)

    def state(self, process):
        parts = self.command(process, 'state').split()
        self.assertEqual(parts[0], 'STATE')
        return tuple(map(int, parts[1:]))

    def await_state(self, process, condition):
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            state = self.state(process)
            if condition(state):
                return state
            time.sleep(.02)
        self.fail('Expected transfer/cache state not reached: ' + repr(state))

    @contextmanager
    def server(self, ttl=4000):
        process = subprocess.Popen(['java', '-cp', self.classes.name,
                                    'os.vortex.tv.LanApkServerLifecycleHarness', str(ttl)],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, text=True)
        try:
            url = urllib.parse.urlsplit(self.line(process))
            self.assertEqual(url.hostname, '127.0.0.1')
            yield process, url
        finally:
            if process.poll() is None:
                process.stdin.write('exit\n')
                process.stdin.flush()
                try:
                    process.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate(timeout=3)
            else:
                process.communicate(timeout=3)

    def connect(self, url):
        return socket.create_connection((url.hostname, url.port), timeout=2)

    def start_upload(self, client, url, size):
        request = (f'POST {url.path.replace("/p/", "/upload/")} HTTP/1.1\r\n'
                   f'Host: {url.netloc}\r\nOrigin: http://{url.netloc}\r\n'
                   'Content-Type: application/vnd.android.package-archive\r\n'
                   f'Content-Length: {size}\r\n\r\n').encode('ascii')
        client.sendall(request + b'PK\x03\x04')

    def assert_peer_closed(self, client):
        client.settimeout(1)
        try:
            data = client.recv(4096)
        except ConnectionResetError:
            return
        self.assertEqual(data, b'', 'Closed/expired transfer produced a response')

    def test_close_interrupts_incomplete_header(self):
        with self.server() as (process, url), self.connect(url) as client:
            client.sendall(b'GET /unfinished')
            time.sleep(.1)
            self.assertEqual(self.command(process, 'close'), 'CLOSED')
            self.assert_peer_closed(client)
            self.assertEqual(self.state(process), (0, 0, 0))

    def test_close_during_body_prevents_late_delivery_and_cleans_cache(self):
        with self.server() as (process, url), self.connect(url) as client:
            self.start_upload(client, url, 8)
            self.await_state(process, lambda state: state == (0, 1, 4))
            # The server is waiting for the rest of this body when close wins.
            time.sleep(.1)
            self.assertEqual(self.command(process, 'close'), 'CLOSED')
            try:
                client.sendall(b'ABCD')
            except (BrokenPipeError, ConnectionResetError):
                pass
            self.assert_peer_closed(client)
            self.assertEqual(self.await_state(process, lambda state: state == (0, 0, 0)),
                             (0, 0, 0))

    def trickle_until_closed(self, client):
        client.settimeout(.05)
        deadline = time.monotonic() + 2.5
        while time.monotonic() < deadline:
            try:
                client.sendall(b'x')
                if not client.recv(4096):
                    return
                self.fail('Incomplete transfer produced a response')
            except (BrokenPipeError, ConnectionResetError):
                return
            except socket.timeout:
                pass
            time.sleep(.05)
        self.fail('Trickled traffic extended the total pairing lifetime')

    def test_trickled_header_cannot_extend_pairing_lifetime(self):
        with self.server(ttl=800) as (process, url), self.connect(url) as client:
            client.sendall(b'GET /')
            self.trickle_until_closed(client)
            self.assertEqual(self.state(process), (0, 0, 0))

    def test_trickled_body_expires_and_removes_partial_apk(self):
        with self.server(ttl=1000) as (process, url), self.connect(url) as client:
            self.start_upload(client, url, 1024)
            self.await_state(process, lambda state: state == (0, 1, 4))
            self.trickle_until_closed(client)
            self.assertEqual(self.await_state(process, lambda state: state == (0, 0, 0)),
                             (0, 0, 0))

    def test_malformed_header_does_not_consume_pairing(self):
        with self.server() as (process, url):
            with self.connect(url) as bad:
                bad.sendall((f'GET {url.path} HTTP/1.1\r\nInvalid header\r\n\r\n').encode())
                self.assertTrue(bad.recv(4096).startswith(b'HTTP/1.1 400'))
            with self.connect(url) as valid:
                valid.sendall((f'GET {url.path} HTTP/1.1\r\nHost: {url.netloc}\r\n\r\n').encode())
                self.assertTrue(valid.recv(4096).startswith(b'HTTP/1.1 200'))
            self.assertEqual(self.state(process), (0, 0, 0))


if __name__ == '__main__':
    unittest.main()
