# coding: utf8

from flask import Blueprint, jsonify

from qgis.core import QgsSimpleFillSymbolLayer
from qgis.core import QgsSimpleLineSymbolLayer


renderers = Blueprint("renderers", __name__)


@renderers.get("/")
def renderers_list():
    return jsonify(["single_symbol"])


@renderers.get("/<geom>/<name>")
def renderers_symbols(name, geom):
    if name != "single_symbol":
        return {"error": "Invalid renderer"}

    if geom == "line":
        props = QgsSimpleLineSymbolLayer().properties()
    elif geom == "polygon":
        props = QgsSimpleFillSymbolLayer().properties()
        props["outline_style"] = (
            "solid (no, solid, dash, dot, dash dot, dash dot dot)"
        )

    return jsonify(props)
