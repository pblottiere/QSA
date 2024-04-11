# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import struct
import pickle
import socket
from osgeo import gdal
from pathlib import Path
from threading import Thread
from datetime import datetime

from qgis import PyQt
from qgis.server import QgsConfigCache
from qgis.utils import server_active_plugins
from qgis.core import Qgis, QgsProviderRegistry, QgsApplication

LOG_MESSAGES = []


def log_messages():
    m = {}
    m["logs"] = "\n".join(LOG_MESSAGES)
    return m


def metadata(iface) -> dict:
    m = {}
    m["plugins"] = server_active_plugins

    m["versions"] = {}
    m["versions"]["qgis"] = f"{Qgis.version().split('-')[0]}"
    m["versions"]["qt"] = PyQt.QtCore.QT_VERSION_STR
    m["versions"]["python"] = sys.version.split(" ")[0]
    m["versions"]["gdal"] = gdal.__version__

    m["providers"] = QgsProviderRegistry.instance().pluginList().split("\n")

    m["cache"] = {}
    m["cache"]["projects"] = []
    for project in QgsConfigCache.instance().projects():
        m["cache"]["projects"].append(Path(project.fileName()).name)

    return m


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

            payload = {}
            if b"metadata" in data:
                payload = metadata(iface)
            elif b"logs" in data:
                payload = log_messages()

            ser = pickle.dumps(payload)
            s.sendall(struct.pack(">I", len(ser)))
            s.sendall(ser)
        except Exception as e:
            print(e, file=sys.stderr)
            s = auto_connect(s, host, port)


def capture_log_message(message, tag, level):
    LOG_MESSAGES.append(message)


def serverClassFactory(iface):
    QgsApplication.instance().messageLog().messageReceived.connect(
        capture_log_message
    )

    host = str(os.environ.get("QSA_HOST", "localhost"))
    port = int(os.environ.get("QSA_PORT", 9999))

    t = Thread(
        target=f,
        args=(
            iface,
            host.replace('"', ""),
            port,
        ),
    )
    t.start()
