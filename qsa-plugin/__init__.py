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
from qgis.utils import server_active_plugins
from qgis.server import QgsConfigCache, QgsServerFilter
from qgis.core import Qgis, QgsProviderRegistry, QgsApplication

LOG_MESSAGES = []


class ProbeFilter(QgsServerFilter):
    def __init__(self, iface, task):
        super().__init__(iface)
        self.task = task

    def onRequestReady(self) -> bool:
        request = self.serverInterface().requestHandler()
        params = request.parameterMap()

        self.task["project"] = params.get("MAP", "")
        self.task["service"] = params.get("SERVICE", "")
        self.task["request"] = params.get("REQUEST", "")
        self.task["start"] = datetime.now()
        self.task["count"] += 1

        return True

    def onResponseComplete(self) -> bool:
        self._clear_task()
        return True

    def onSendResponse(self) -> bool:
        self._clear_task()
        return True

    def _clear_task(self):
        count = self.task["count"]
        self.task.clear()
        self.task["count"] = count


def log_messages():
    m = {}
    m["logs"] = "\n".join(LOG_MESSAGES)
    return m


def stats(task):
    s = task
    if "start" in s:
        s["duration"] = int(
            (datetime.now() - s["start"]).total_seconds() * 1000
        )
    return s


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


def f(iface, host: str, port: int, task: dict) -> None:
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
            elif b"stats" in data:
                payload = stats(task)

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

    task = {}
    task["count"] = 0

    t = Thread(
        target=f,
        args=(
            iface,
            host.replace('"', ""),
            port,
            task,
        ),
    )
    t.start()

    iface.registerFilter(ProbeFilter(iface, task), 100)
