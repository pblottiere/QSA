# coding: utf8

from flask import Blueprint, jsonify, request

from ..project import QSAProject


projects = Blueprint("projects", __name__)


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
        current = eval(data["current"])
        style_name = data["name"]
        rc, msg = project.layer_update_style(layer_name, style_name, current)
        if not rc:
            return {"error": msg}, 415
        return jsonify(True), 201
    else:
        return {"error": "Project does not exist"}, 415


@projects.post("/<name>/styles")
def project_add_style(name):
    project = QSAProject(name)
    if project.exists():
        data = request.get_json()
        if "name" not in data or "type" not in data or "symbology" not in data:
            return {"error": "Invalid parameters"}, 415

        line_width = -1
        if data["type"] == "line":
            if "width" not in data or "color" not in data:
                return {"error": "Invalid parameters"}, 415
            line_width = data["width"]

        polygon_stroke_width = -1
        polygon_stroke_color = -1
        if data["type"] == "polygon":
            if (
                "color" not in data
                or "stroke_color" not in data
                or "stroke_width" not in data
            ):
                return {"error": "Invalid parameters"}, 415
            polygon_stroke_color = data["stroke_color"]
            polygon_stroke_width = data["stroke_width"]

        rc = project.add_style(
            data["name"],
            data["type"],
            data["symbology"],
            data["color"],
            line_width,
            polygon_stroke_color,
            polygon_stroke_width,
        )
        return jsonify(rc), 201
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
        project.add_layer(data["datasource"], data["name"], data["crs"])
        return jsonify(True), 201
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
