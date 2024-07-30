# coding: utf8

from flask import Blueprint, jsonify

from qgis.core import (
    QgsStyle,
    QgsSimpleLineSymbolLayer,
    QgsSimpleFillSymbolLayer,
    QgsSingleBandGrayRenderer,
    QgsMultiBandColorRenderer,
    QgsSimpleMarkerSymbolLayer,
    QgsSingleBandPseudoColorRenderer,
)

from ..utils import logger
from .utils import log_request


symbology = Blueprint("symbology", __name__)


@symbology.get("/vector/line/single_symbol/line/properties")
def symbology_symbols_line():
    log_request()
    try:
        props = QgsSimpleLineSymbolLayer().properties()
        return jsonify(props)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@symbology.get("/vector/polygon/single_symbol/fill/properties")
def symbology_symbols_fill():
    log_request()
    try:
        props = QgsSimpleFillSymbolLayer().properties()
        props["outline_style"] = (
            "solid (no, solid, dash, dot, dash dot, dash dot dot)"
        )
        return jsonify(props)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@symbology.get("/vector/point/single_symbol/marker/properties")
def symbology_symbols_marker():
    log_request()
    try:
        props = QgsSimpleMarkerSymbolLayer().properties()
        props["outline_style"] = (
            "solid (no, solid, dash, dot, dash dot, dash dot dot)"
        )
        return jsonify(props)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@symbology.get("/vector/rendering/properties")
def symbology_vector_rendering():
    log_request()
    try:
        props = {}
        props["opacity"] = 100.0
        return jsonify(props)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@symbology.get(
    f"/raster/{QgsSingleBandGrayRenderer(None, 1).type()}/properties"
)
def symbology_raster_singlebandgray():
    log_request()
    try:
        props = {}
        props["gray"] = {"band": 1, "min": 0.0, "max": 1.0}
        props["contrast_enhancement"] = {
            "algorithm": "NoEnhancement (StretchToMinimumMaximum, NoEnhancement)",
            "limits_min_max": "MinMax (MinMax, UserDefined)",
        }
        props["color_gradient"] = "BlackToWhite (BlackToWhite, WhiteToBlack)"
        return jsonify(props)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@symbology.get(
    f"/raster/{QgsMultiBandColorRenderer(None, 1, 1, 1).type()}/properties"
)
def symbology_raster_multibandcolor():
    log_request()
    try:
        props = {}
        props["red"] = {"band": 1, "min": 0.0, "max": 1.0}
        props["green"] = {"band": 2, "min": 0.0, "max": 1.0}
        props["blue"] = {"band": 3, "min": 0.0, "max": 1.0}
        props["contrast_enhancement"] = {
            "algorithm": "NoEnhancement (StretchToMinimumMaximum, NoEnhancement)",
            "limits_min_max": "MinMax (MinMax, UserDefined)",
        }
        return jsonify(props)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@symbology.get(
    f"/raster/{QgsSingleBandPseudoColorRenderer(None, 1).type()}/properties"
)
def symbology_raster_singlebandpseudocolor():
    log_request()
    try:
        ramps = ", ".join(QgsStyle().defaultStyle().colorRampNames())

        props = {}
        props["band"] = {"band": 1, "min": 0.0, "max": 1.0}
        props["ramp"] = {
            "name": f"Spectral ({ramps})",
            "color1": "0,0,0,255",
            "color2": "255,255,255,255",
            "stops": "0.2;2,2,11,255:0.8;200,200,110,255",
            "interpolation": "Linear (Linear, Discrete, Exact)",
        }
        props["contrast_enhancement"] = {
            "limits_min_max": "MinMax (MinMax, UserDefined)",
        }
        return jsonify(props)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@symbology.get(
    f"/raster/{QgsSingleBandPseudoColorRenderer(None, 1).type()}/ramp/<name>/properties"
)
def symbology_raster_singlebandpseudocolor_ramp_props(name):
    log_request()
    try:
        proper_name = ""
        for n in QgsStyle().defaultStyle().colorRampNames():
            if n.lower() == name:
                proper_name = n

        props = {}
        ramp = QgsStyle().defaultStyle().colorRamp(proper_name)
        if ramp:
            props["color1"] = ramp.properties()["color1"].split("rgb")[0]
            props["color2"] = ramp.properties()["color2"].split("rgb")[0]

        return jsonify(props)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@symbology.get("/raster/rendering/properties")
def symbology_raster_rendering():
    log_request()
    try:
        props = {}
        props["gamma"] = 1.0
        props["brightness"] = 0
        props["contrast"] = 0
        props["saturation"] = 0
        return jsonify(props)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415
