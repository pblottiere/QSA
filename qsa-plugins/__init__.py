# -*- coding: utf-8 -*-

"""
QGIS Plugin for monitoring performances.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Paul Blottiere"
__contact__ = "blottiere.paul@gmail.com"
__copyright__ = "Copyright 2019, Paul Blottiere"
__date__ = "2019/07/19"
__email__ = "blottiere.paul@gmail.com"
__license__ = "GPLv3"

import socket
import time
import datetime
from threading import Thread
from multiprocessing import Process

import requests

IFACE=None


def auto_connect(s, host, port):
    while True:
        print("try to connect...")
        try:
            s.connect((host, port))
            break
        except Exception as e:
            print(e)
            if e.errno == 106:
                s.close()
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        time.sleep(1)
    return s


def f(iface, host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s = auto_connect(s, host, port)

    while True:
        try:
            data = s.recv(2000)
            print(data)

            print("send ack...")
            s.send(b"ACK")
            print("sent!")
        except Exception as e:
            print(e)
            s = auto_connect(s, host, port)


def serverClassFactory(iface):
    """Load Snail class from file Snail.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    # from .qsa import QSA

    # print("COUCOU")
    # print(iface.configFilePath())
    # IFACE=iface
    # p = Process(target=f, args=(iface,))
    # p.start()

    t = Thread( target=f, args=(iface, "127.0.0.1", 9999,) )
    t.start()

    # while True:
    #     print(datetime.datetime.now())
    #     entry = iface.configFilePath()
    #     print(entry)
    #     iface.reloadSettings()
    #     time.sleep(10)
