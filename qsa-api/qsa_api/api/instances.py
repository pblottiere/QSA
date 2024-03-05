# coding: utf8

from flask import Blueprint
from flask import current_app

instances = Blueprint("instances", __name__)


@instances.get("/")
def instances_list():
    monitor = current_app.config["MONITOR"]

    if not monitor:
        return {"error": "QGIS Server monitoring is not activated"}, 415

    conns = []
    for uid in monitor.conns:
        info = {}
        info["SERVER ID"] = uid
        info["IP"] = monitor.conns[uid].ip
        conns.append(info)
    return conns
