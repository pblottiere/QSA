# coding: utf8

from jsonschema import validate
from flask import Blueprint, jsonify, request
from jsonschema.exceptions import ValidationError

from ..project import QSAProject
from ..processing import RasterCalculator, Histogram


processing = Blueprint("processing", __name__)


@processing.post("/raster/calculator/<project>")
def raster_calculator(project: str):
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


@processing.get("/raster/histogram/<project>/<layer>")
def raster_histogram(project: str, layer: str):
   proj = QSAProject(project)
   if proj.exists():
      layer_infos = proj.layer(layer)
      if layer_infos:
         if "type" in layer_infos and layer_infos["type"] != "raster":
            return {"error": "Histogram is available for raster layer only"}
         histo = Histogram(proj._qgis_project_uri, layer)
         return jsonify(histo.process()), 201
      else:
         return {"error": "Layer does not exist"}, 415
   else:
      return {"error": "Project does not exist"}, 415
