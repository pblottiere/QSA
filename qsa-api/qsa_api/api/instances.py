# coding: utf8

from flask import current_app
from flask import Blueprint, jsonify

instances = Blueprint("instances", __name__)


@instances.get("/")
def instances_list():
    monitor = current_app.config["MONITOR"]

    if not monitor:
        return {"error": "QGIS Server monitoring is not activated"}, 415

    conns = []
    print(monitor.conns)
    for con in monitor.conns:
        info = {}
        info["ip"] = con.ip
        info["port"] = con.port
        conns.append(info)
    return conns
