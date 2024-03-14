# coding: utf8

import sys
import uuid
import time
import pickle
import socket
import struct
from datetime import datetime
from threading import Thread, Lock

from qgis.core import Qgis

from qsa_api.config import QSAConfig


class QSAMonitorThread(Thread):
    def __init__(self, con, ip: str, port: int) -> None:
        Thread.__init__(self)
        self.con = con
        self.ip = ip
        self.port = port
        self.now = datetime.now()
        self.response = None

    def run(self):
        try:
            while True:
                # empty recv if error or size of the payload
                data = self.con.recv(4)

                if not data:
                    self.con.close()
                    return

                data_size = struct.unpack('>I', data)[0]
                self.response = self._recv_payload(data_size)

        except BrokenPipeError:
            return

    @property
    def metadata(self) -> dict:
        self.response = None
        try:
            self.con.send(b"metadata")
            return self._wait_recv()
        except Exception:
            return {}

    @property
    def logs(self) -> dict:
        self.response = None
        try:
            self.con.send(b"logs")
            return self._wait_recv()
        except Exception as e:
            print(e, file=sys.stderr)
            return {}

    def _wait_recv(self):
        it = 0

        while True:
            if self.response:
                return self.response

            time.sleep(0.1)
            it += 1

            if it >= 20:
                return {"error": "timeout"}

    def _recv_payload(self, data_size):
        received_payload = b""
        reamining_payload_size = data_size
        while reamining_payload_size != 0:
            received_payload += self.con.recv(reamining_payload_size)
            reamining_payload_size = data_size - len(received_payload)
        return pickle.loads(received_payload)


class QSAMonitor:
    def __init__(self, cfg: QSAConfig) -> None:
        self.monitor: Thread
        self.port: int = cfg.monitoring_port

        self._lock = Lock()
        self._conns: dict = {}

    @property
    def conns(self):
        conns = {}
        self._lock.acquire()
        for uid in self._conns:
            if self._conns[uid].is_alive():
                conns[uid] = self._conns[uid]
            else:
                self._conns[uid].join()
        self._conns = conns
        self._lock.release()
        return self._conns

    def start(self) -> None:
        self.monitor = Thread(target=self._start, args=())
        self.monitor.start()

    def _start(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", self.port))

        while True:
            s.listen(5)
            try:
                (con, (ip, port)) = s.accept()
            except:
                break

            thread = QSAMonitorThread(con, ip, port)
            thread.start()

            self._lock.acquire()
            uid = str(uuid.uuid4())[:8]
            self._conns[uid] = thread
            self._lock.release()

        for uid in self._conns:
            self._conns[uid].join()
