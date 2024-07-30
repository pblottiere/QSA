# coding: utf8

from flask import Blueprint
from flask import current_app
from datetime import datetime

from .utils import log_request


instances = Blueprint("instances", __name__)


@instances.get("/")
def instances_list():
    log_request()
    try:
        monitor = current_app.config["MONITOR"]

        if not monitor:
            return {"error": "QGIS Server monitoring is not activated"}, 415

        conns = {"servers": []}
        for uid in monitor.conns:
            info = {}
            info["id"] = uid
            info["ip"] = monitor.conns[uid].ip

            d = datetime.now() - monitor.conns[uid].now
            info["binded"] = int(d.total_seconds())
            conns["servers"].append(info)
        return conns
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@instances.get("/<instance>")
def instances_metadata(instance):
    log_request()
    try:
        monitor = current_app.config["MONITOR"]

        if not monitor:
            return {"error": "QGIS Server monitoring is not activated"}, 415

        if instance not in monitor.conns:
            return {"error": "QGIS Server instance is not available"}, 415

        return monitor.conns[instance].metadata
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@instances.get("/<instance>/logs")
def instances_logs(instance):
    log_request()
    try:
        monitor = current_app.config["MONITOR"]

        if not monitor:
            return {"error": "QGIS Server monitoring is not activated"}, 415

        if instance not in monitor.conns:
            return {"error": "QGIS Server instance is not available"}, 415

        return monitor.conns[instance].logs
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@instances.get("/<instance>/stats")
def instances_stats(instance):
    log_request()
    try:
        monitor = current_app.config["MONITOR"]

        if not monitor:
            return {"error": "QGIS Server monitoring is not activated"}, 415

        if instance not in monitor.conns:
            return {"error": "QGIS Server instance is not available"}, 415

        return monitor.conns[instance].stats
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415
