# coding: utf8

import socket
from threading import Thread, Lock
from socketserver import ThreadingMixIn

from qsa_api.config import Config


class QSAMonitorThread(Thread):
    def __init__(self, con, ip: str, port: int) -> None:
        Thread.__init__(self)
        self.con = con
        self.ip = ip
        self.port = port

    def run(self):
        try:
            while True :
                data = self.con.recv(2048)

                if not data:
                    self.con.close()
                    return

                # self.con.send(msg)
        except BrokenPipeError:
            return


class QSAMonitor:

    def __init__(self, cfg: Config) -> None:
        self.monitor : Thread
        self.port : int = cfg.admin_port

        self._lock = Lock()
        self._conns : list[Thread] = []

    @property
    def conns(self):
        conns = []
        self._lock.acquire()
        for con in self._conns:
            if con.is_alive():
                conns.append(con)
            else:
                con.join()
        self._conns = conns
        self._lock.release()
        return self._conns

    def start(self) -> None:
        self.monitor = Thread(target=self._start, args=())
        self.monitor.start()

    def _start(self) -> None:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', self.port))

        while True:
            s.listen(5)
            try:
                (con, (ip,port)) = s.accept()
            except:
                break

            thread = QSAMonitorThread(con, ip, port)
            thread.start()

            self._lock.acquire()
            self._conns.append(thread)
            self._lock.release()

        for t in self._conns:
            t.join()
