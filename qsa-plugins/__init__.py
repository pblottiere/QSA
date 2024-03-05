# -*- coding: utf-8 -*-

import os
import sys
import time
import socket
from threading import Thread


def auto_connect(s: socket.socket, host: str, port: int) -> socket.socket:
    while True:
        print("Try to connect...", file=sys.stderr)
        try:
            s.connect((host, port))
            break
        except Exception as e:
            if e.errno == 106:
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(5)
    print("Connected with QSA server", file=sys.stderr)
    return s


def f(iface, host: str, port: int) -> None:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = auto_connect(s, host, port)

    while True:
        try:
            data = s.recv(2000)
            s.send(b"ACK")
        except Exception:
            s = auto_connect(s, host, port)


def serverClassFactory(iface):
    host = str(os.environ.get("QSA_HOST", "localhost"))
    port = int(os.environ.get("QSA_PORT", 9999))

    t = Thread(
        target=f,
        args=(
            iface,
            host.replace("\"", ""),
            port,
        ),
    )
    t.start()
