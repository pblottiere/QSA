# coding: utf8

from flask import Blueprint
from flask import current_app
from datetime import datetime

instances = Blueprint("instances", __name__)


@instances.get("/")
def instances_list():
    monitor = current_app.config["MONITOR"]

    if not monitor:
        return {"error": "QGIS Server monitoring is not activated"}, 415

    conns = {"servers" : []}
    for uid in monitor.conns:
        info = {}
        info["id"] = uid
        info["ip"] = monitor.conns[uid].ip

        d = datetime.now() - monitor.conns[uid].now
        info["binded"] = int(d.total_seconds())
        conns["servers"].append(info)
    return conns


@instances.get("/<instance>")
def instances_metadata(instance):
    monitor = current_app.config["MONITOR"]

    if not monitor:
        return {"error": "QGIS Server monitoring is not activated"}, 415

    if instance not in monitor.conns:
        return {"error": "QGIS Server instance is not available"}, 415

    return monitor.conns[instance].metadata
