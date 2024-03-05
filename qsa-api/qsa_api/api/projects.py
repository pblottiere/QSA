# coding: utf8

import shutil
import requests
from flask import send_file, Blueprint, jsonify, request

from ..wms import WMS
from ..project import QSAProject


projects = Blueprint("projects", __name__)


def str_to_bool(s: str) -> bool:
    if s in ["True", "TRUE", "true", 1]:
        return True
    return False


@projects.get("/")
def projects_list():
    p = []
    for project in QSAProject.projects():
        p.append(project.name)
    return jsonify(p)


@projects.get("/<name>")
def project_info(name: str):
    project = QSAProject(name)

    if project.exists():
        return jsonify(QSAProject(name).metadata)
    return {"error": "Project does not exist"}, 415


@projects.post("/")
def project_add():
    if request.is_json:
        if "name" not in request.get_json():
            return {"error": "Parameter 'name' is missing"}, 415

        if "author" not in request.get_json():
            return {"error": "Parameter 'author' is missing"}, 415

        name = request.get_json()["name"]
        author = request.get_json()["author"]

        project = QSAProject(name)
        if project.exists():
            return {"error": "Project already exists"}
        project.create(author)
        return jsonify(True), 201
    return {"error": "Request must be JSON"}, 415


@projects.delete("/<name>")
def project_del(name):
    project = QSAProject(name)
    if project.exists():
        project.remove()
        return jsonify(True), 201
    return {"error": "Project does not exist"}, 415


@projects.get("/<name>/styles")
def project_styles(name):
    project = QSAProject(name)
    if project.exists():
        return jsonify(project.styles), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/styles/<style>")
def project_style(name, style):
    project = QSAProject(name)
    if project.exists():
        infos = project.style(style)
        return jsonify(infos), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.delete("/<name>/styles/<style>")
def project_del_style(name, style):
    project = QSAProject(name)
    if project.exists():
        if style in project.styles:
            rc = project.remove_style(style)
            return jsonify(rc), 201
        else:
            return {"error": "Style does not exist"}, 415
    else:
        return {"error": "Project does not exist"}, 415


@projects.post("/<name>/layers/<layer_name>/style")
def project_layer_update_style(name, layer_name):
    project = QSAProject(name)
    if project.exists():
        data = request.get_json()
        if "current" not in data or "name" not in data:
            return {"error": "Invalid parameters"}, 415

        current = str_to_bool(data["current"])

        style_name = data["name"]
        rc, msg = project.layer_update_style(layer_name, style_name, current)
        if not rc:
            return {"error": msg}, 415
        return jsonify(True), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/layers/<layer_name>/map/url")
def project_layer_map_url(name, layer_name):
    project = QSAProject(name)
    if project.exists():
        getmap = WMS.getmap_url(name, layer_name)
        return jsonify({"url": getmap}), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/layers/<layer_name>/map")
def project_layer_map(name, layer_name):
    project = QSAProject(name)
    if project.exists():
        url = WMS.getmap(name, layer_name)
        r = requests.get(url, stream=True)

        png = "/tmp/map.png"
        with open(png, "wb") as out_file:
            shutil.copyfileobj(r.raw, out_file)

        return send_file(png, mimetype="image/png")
    else:
        return {"error": "Project does not exist"}, 415


@projects.post("/<name>/styles")
def project_add_style(name):
    project = QSAProject(name)
    if project.exists():
        data = request.get_json()

        if (
            "name" not in data
            or "symbol" not in data
            or "symbology" not in data
        ):
            return {"error": "Invalid parameters"}, 415

        # legacy support
        symbology = data["symbology"]
        if symbology == "single symbol":
            symbology = "single_symbol"

        rc = project.add_style(
            data["name"],
            data["symbol"],
            data["symbology"],
            data["properties"],
        )
        return jsonify(rc), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/styles/default")
def project_default_styles(name):
    project = QSAProject(name)
    if project.exists():
        infos = project.default_styles()
        return jsonify(infos), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.post("/<name>/styles/default")
def project_update_default_style(name):
    project = QSAProject(name)
    if project.exists():
        data = request.get_json()
        if (
            "geometry" not in data
            or "symbology" not in data
            or "symbol" not in data
            or "style" not in data
        ):
            return {"error": "Invalid parameters"}, 415

        project.style_update(
            data["geometry"], data["symbology"], data["symbol"], data["style"]
        )
        return jsonify(True), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/layers")
def project_layers(name):
    project = QSAProject(name)
    if project.exists():
        return jsonify(project.layers), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.post("/<name>/layers")
def project_add_layer(name):
    project = QSAProject(name)
    if project.exists():
        data = request.get_json()
        rc = project.add_layer(data["datasource"], data["name"], data["crs"])
        return jsonify(rc), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.get("/<name>/layers/<layer_name>")
def project_info_layer(name, layer_name):
    project = QSAProject(name)
    if project.exists():
        layer_infos = project.layer(layer_name)
        if layer_infos:
            return jsonify(layer_infos), 201
        else:
            return {"error": "Layer does not exist"}, 415
    else:
        return {"error": "Project does not exist"}, 415


@projects.delete("/<name>/layers/<layer_name>")
def project_del_layer(name, layer_name):
    project = QSAProject(name)
    if project.exists():
        if project.layer_exists(layer_name):
            rc = project.remove_layer(layer_name)
            return jsonify(rc), 201
        else:
            return {"error": "Layer does not exist"}, 415
    else:
        return {"error": "Project does not exist"}, 415
