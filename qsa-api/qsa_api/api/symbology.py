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


@symbology.get("/vector/rendering/properties")
def symbology_vector_rendering():
    props = {}
    props["opacity"] = 100.0
    return jsonify(props)


@symbology.get(
    f"/raster/{QgsSingleBandGrayRenderer(None, 1).type()}/properties"
)
def symbology_raster_singlebandgray():
    props = {}
    props["gray"] = {"band": 1, "min": 0.0, "max": 1.0}
    props["contrast_enhancement"] = {
        "algorithm": "NoEnhancement (StretchToMinimumMaximum, NoEnhancement)",
        "limits_min_max": "MinMax (MinMax, UserDefined)",
    }
    props["color_gradient"] = "BlackToWhite (BlackToWhite, WhiteToBlack)"
    return jsonify(props)


@symbology.get(
    f"/raster/{QgsMultiBandColorRenderer(None, 1, 1, 1).type()}/properties"
)
def symbology_raster_multibandcolor():
    props = {}
    props["red"] = {"band": 1, "min": 0.0, "max": 1.0}
    props["green"] = {"band": 2, "min": 0.0, "max": 1.0}
    props["blue"] = {"band": 3, "min": 0.0, "max": 1.0}
    props["contrast_enhancement"] = {
        "algorithm": "NoEnhancement (StretchToMinimumMaximum, NoEnhancement)",
        "limits_min_max": "MinMax (MinMax, UserDefined)",
    }
    return jsonify(props)


@symbology.get(
    f"/raster/{QgsSingleBandPseudoColorRenderer(None, 1).type()}/properties"
)
def symbology_raster_singlebandpseudocolor():
    ramps = ", ".join(QgsStyle().defaultStyle().colorRampNames())

    props = {}
    props["band"] = {"band": 1, "min": 0.0, "max": 1.0}
    props["ramp"] = {
            "name" : f"Spectral ({ramps})",
            "interpolation": "Linear (Linear, Discrete, Exact)"
    }
    props["contrast_enhancement"] = {
        "algorithm": "NoEnhancement (StretchToMinimumMaximum, NoEnhancement)",
        "limits_min_max": "MinMax (MinMax, UserDefined)",
    }
    return jsonify(props)



@symbology.get("/raster/rendering/properties")
def symbology_raster_rendering():
    props = {}
    props["gamma"] = 1.0
    props["brightness"] = 0
    props["contrast"] = 0
    props["saturation"] = 0
    return jsonify(props)
