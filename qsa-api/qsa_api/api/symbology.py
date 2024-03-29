# coding: utf8

from flask import Blueprint, jsonify

from qgis.core import QgsSimpleFillSymbolLayer
from qgis.core import QgsSimpleLineSymbolLayer
from qgis.core import QgsSimpleMarkerSymbolLayer


symbology = Blueprint("symbology", __name__)


@symbology.get("/vector/line/single_symbol/line/properties")
def symbology_symbols_line():
    props = QgsSimpleLineSymbolLayer().properties()
    return jsonify(props)


@symbology.get("/vector/polygon/single_symbol/fill/properties")
def symbology_symbols_fill():
    props = QgsSimpleFillSymbolLayer().properties()
    props["outline_style"] = (
        "solid (no, solid, dash, dot, dash dot, dash dot dot)"
    )
    return jsonify(props)


@symbology.get("/vector/point/single_symbol/marker/properties")
def symbology_symbols_marker():
    props = QgsSimpleMarkerSymbolLayer().properties()
    props["outline_style"] = (
        "solid (no, solid, dash, dot, dash dot, dash dot dot)"
    )
    return jsonify(props)
