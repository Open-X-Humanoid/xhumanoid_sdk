#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check that the browser viewer of the simulator is serving the scene.

Run inside the sim container while sim.launch.py is running with
viewer_port:=<port>. It waits for the HTTP page, opens the websocket the way a
browser would, and checks that

  * the initial scene arrives (the meshes of the robot and hands are several
    MB), and
  * messages keep arriving afterwards (the pose updates at about 30 Hz).

Usage: check_viewer.py <port>
"""

import sys
import time
import urllib.request

import viser
from websockets.sync.client import connect

MIN_SCENE_BYTES = 1_000_000   # the meshes of the robot alone are larger
LISTEN_S = 6.0
TAIL_S = 2.0                  # updates must still arrive in the last TAIL_S


def wait_http(url: str, timeout: float) -> None:
    end = time.time() + timeout
    while True:
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                if resp.status == 200:
                    return
        except OSError:
            pass
        if time.time() > end:
            raise SystemExit(f'VIEWER CHECK FAILED: {url} not reachable')
        time.sleep(0.5)


def listen(port: int):
    """Return (total bytes, frames, frames in the last TAIL_S seconds)."""
    total, frames, tail = 0, 0, 0
    start = time.time()
    end = start + LISTEN_S
    # The server only accepts clients that announce the viser version they
    # match. The initial scene is one message of several MB, so lift the limit.
    with connect(f'ws://127.0.0.1:{port}', open_timeout=10, max_size=None,
                 subprotocols=[f'viser-v{viser.__version__}']) as ws:
        while time.time() < end:
            try:
                data = ws.recv(timeout=1.0)
            except TimeoutError:
                continue
            if not isinstance(data, bytes):
                continue
            total += len(data)
            frames += 1
            if time.time() > end - TAIL_S:
                tail += 1
    return total, frames, tail


def main():
    port = int(sys.argv[1])
    wait_http(f'http://127.0.0.1:{port}/', 40)
    total, frames, tail = listen(port)
    print(f'viewer: HTTP 200, {frames} websocket messages, '
          f'{total / 1e6:.1f} MB, {tail} in the last {TAIL_S:.0f} s')
    if total < MIN_SCENE_BYTES or tail == 0:
        print('VIEWER CHECK FAILED')
        sys.exit(1)
    print('VIEWER CHECK PASSED')


if __name__ == '__main__':
    main()
