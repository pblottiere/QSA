# coding: utf8

from jsonschema import validate
from flask import Blueprint, jsonify, request
from jsonschema.exceptions import ValidationError

from ..utils import logger
from ..project import QSAProject
from ..processing import RasterCalculator, Histogram

from .utils import log_request


processing = Blueprint("processing", __name__)


@processing.post("/raster/calculator/<project>")
def raster_calculator(project: str):
    log_request()
    try:
        schema = {
            "type": "object",
            "required": ["expression", "output"],
            "properties": {
                "expression": {"type": "string"},
                "output": {"type": "string"},
            },
        }

        data = request.get_json()
        try:
            validate(data, schema)
        except ValidationError as e:
            return {"error": e.message}, 415

        expression = data["expression"]
        output = data["output"]

        psql_schema = request.args.get("schema", default="public")
        proj = QSAProject(project, psql_schema)

        if not proj.exists():
            return {"error": "Project doesn't exist"}, 415

        calc = RasterCalculator(proj._qgis_project_uri, expression)
        if not calc.is_valid():
            return {"error": "Invalid expression"}, 415

        rc, msg = calc.process(output)
        if not rc:
            return {
                "error": f"Raster calculator failed to process expression ({msg})"
            }, 415

        return jsonify(rc), 201
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@processing.post("/raster/histogram/<project>/<layer>")
def raster_histogram(project: str, layer: str):
    log_request()
    try:
        schema = {
            "type": "object",
            "properties": {
                "min": {"type": "number"},
                "max": {"type": "number"},
                "count": {"type": "number"},
            },
        }

        data = request.get_json()
        try:
            validate(data, schema)
        except ValidationError as e:
            return {"error": e.message}, 415

        mini = None
        if "min" in data:
            mini = data["min"]

        maxi = None
        if "max" in data:
            maxi = data["max"]

        count = 1000
        if "count" in data:
            count = data["count"]

        proj = QSAProject(project)
        if proj.exists():
            layer_infos = proj.layer(layer)
            if layer_infos:
                if "type" in layer_infos and layer_infos["type"] != "raster":
                    return {
                        "error": "Histogram is available for raster layer only"
                    }
                histo = Histogram(proj._qgis_project_uri, layer)
                return jsonify(histo.process(mini, maxi, count)), 201
            else:
                return {"error": "Layer does not exist"}, 415
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415
