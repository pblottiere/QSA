# coding: utf8

import shutil
import requests
from jsonschema import validate
from jsonschema.exceptions import ValidationError
from flask import send_file, Blueprint, jsonify, request

from qgis.PyQt.QtCore import QDateTime

from ..wms import WMS
from ..utils import logger
from ..project import QSAProject

from .utils import log_request


projects = Blueprint("projects", __name__)


@projects.get("/")
def projects_list():
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")

        p = []
        for project in QSAProject.projects(psql_schema):
            p.append(project.name)
        return jsonify(p)
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.get("/<name>")
def project_info(name: str):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)

        if project.exists():
            return jsonify(project.metadata)
        return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.post("/")
def project_add():
    log_request()
    try:
        schema = {
            "type": "object",
            "required": ["name", "author"],
            "properties": {
                "name": {"type": "string"},
                "author": {"type": "string"},
                "schema": {"type": "string"},
            },
        }

        if request.is_json:
            data = request.get_json()
            try:
                validate(data, schema)
            except ValidationError as e:
                return {"error": e.message}, 415

            name = data["name"]
            author = data["author"]
            schema = ""
            if "schema" in data:
                schema = data["schema"]

            project = QSAProject(name, schema)
            if project.exists():
                return {"error": "Project already exists"}
            rc, err = project.create(author)
            if not rc:
                return {"error": err}, 415
            return jsonify(True), 201
        return {"error": "Request must be JSON"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.delete("/<name>")
def project_del(name):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)

        if project.exists():
            project.remove()
            return jsonify(True), 201
        return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.get("/<name>/styles")
def project_styles(name):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            return jsonify(project.styles), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.get("/<name>/styles/<style>")
def project_style(name, style):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            infos, err = project.style(style)
            if err:
                return {"error": err}, 415
            else:
                return jsonify(infos), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.delete("/<name>/styles/<style>")
def project_del_style(name, style):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            if style in project.styles:
                rc, msg = project.remove_style(style)
                if not rc:
                    return {"error": msg}, 415
                return jsonify(rc), 201
            else:
                return {"error": "Style does not exist"}, 415
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.post("/<name>/layers/<layer_name>/style")
def project_layer_update_style(name, layer_name):
    log_request()
    try:
        schema = {
            "type": "object",
            "required": ["name", "current"],
            "properties": {
                "name": {"type": "string"},
                "current": {"type": "boolean"},
            },
        }

        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            data = request.get_json()
            try:
                validate(data, schema)
            except ValidationError as e:
                return {"error": e.message}, 415

            current = data["current"]
            style_name = data["name"]
            rc, msg = project.layer_update_style(
                layer_name, style_name, current
            )
            if not rc:
                return {"error": msg}, 415
            return jsonify(True), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.get("/<name>/layers/<layer_name>/map/url")
def project_layer_map_url(name, layer_name):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            getmap = WMS.getmap_url(name, psql_schema, layer_name)
            return jsonify({"url": getmap}), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.get("/<name>/layers/<layer_name>/map")
def project_layer_map(name, layer_name):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            url = WMS.getmap(name, psql_schema, layer_name)
            r = requests.get(url, stream=True)

            png = "/tmp/map.png"
            with open(png, "wb") as out_file:
                shutil.copyfileobj(r.raw, out_file)

            return send_file(png, mimetype="image/png")
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.post("/<name>/styles")
def project_add_style(name):
    log_request()
    try:
        schema = {
            "type": "object",
            "required": ["name", "type", "rendering", "symbology"],
            "properties": {
                "name": {"type": "string"},
                "type": {"type": "string"},
                "symbology": {"type": "object"},
                "rendering": {"type": "object"},
            },
        }

        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            data = request.get_json()
            try:
                validate(data, schema)
            except ValidationError as e:
                return {"error": e.message}, 415

            rc, err = project.add_style(
                data["name"],
                data["type"],
                data["symbology"],
                data["rendering"],
            )
            if rc:
                return jsonify(rc), 201
            else:
                return {"error": err}, 415
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.get("/<name>/styles/default")
def project_default_styles(name: str) -> dict:
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            infos = project.default_styles()
            return jsonify(infos), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.post("/<name>/styles/default")
def project_update_default_style(name):
    log_request()
    try:
        schema = {
            "type": "object",
            "required": ["geometry", "style"],
            "properties": {
                "geometry": {"type": "string"},
                "style": {"type": "string"},
            },
        }

        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            data = request.get_json()
            try:
                validate(data, schema)
            except ValidationError as e:
                return {"error": e.message}, 415

            project.style_update(data["geometry"], data["style"])
            return jsonify(True), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.get("/<name>/layers")
def project_layers(name):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            return jsonify(project.layers), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.post("/<name>/layers")
def project_add_layer(name):
    log_request()
    try:
        schema = {
            "type": "object",
            "required": ["name", "datasource", "type"],
            "properties": {
                "name": {"type": "string"},
                "datasource": {"type": "string"},
                "crs": {"type": "number"},
                "type": {"type": "string"},
                "overview": {"type": "boolean"},
                "datetime": {"type": "string"},
            },
        }

        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)

        if project.exists():
            data = request.get_json()
            try:
                validate(data, schema)
            except ValidationError as e:
                return {"error": e.message}, 415

            crs = -1
            if "crs" in data:
                crs = int(data["crs"])

            overview = False
            if "overview" in data:
                overview = data["overview"]

            datetime = None
            if "datetime" in data:
                # check format "yyyy-MM-dd HH:mm:ss"
                datetime = QDateTime.fromString(
                    data["datetime"], "yyyy-MM-dd HH:mm:ss"
                )
                if not datetime.isValid():
                    return {"error": "Invalid datetime"}, 415

            rc, err = project.add_layer(
                data["datasource"],
                data["type"],
                data["name"],
                crs,
                overview,
                datetime,
            )
            if rc:
                return jsonify(rc), 201
            else:
                return {"error": err}, 415
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.get("/<name>/layers/<layer_name>")
def project_info_layer(name, layer_name):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            layer_infos = project.layer(layer_name)
            if layer_infos:
                return jsonify(layer_infos), 201
            else:
                return {"error": "Layer does not exist"}, 415
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415
    
@projects.get("/<name>/layers/wms")
def project_layers_wms(name):
    """
    Get all published WMS layers
    """
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            return jsonify(project.layers_wms), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415
    
@projects.get("/<name>/layers/wms/feature-info")
def project_wms_feature_info(name):
    """
    Information about the WMS Feature Info settings
    """
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            return jsonify(project.project_wms_feature_info), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415

    
@projects.get("/<name>/layers/wfs")
def project_layers_wfs(name):
    """
    Get all published WFS layers
    """
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            return jsonify(project.layers_wfs_info), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415

@projects.get("/<name>/layers/<layer_name>/wfs")
def project_info_layer_wfs(name, layer_name):
    """
    Get information about a single WFS layer
    """
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            return jsonify(project.layer_wfs(layer_name)), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415

@projects.get("/<name>/layers/<layer_name>/wms")
def project_info_layer_wms(name, layer_name):
    """
    Get information about a single WMS layer
    """
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            return jsonify(project.layer_wms(layer_name)), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415

@projects.post("/<name>/layers/<layer_name>/wfs")
def project_publish_wfs_layer(name, layer_name):
    """
    Change WFS publication status of an vector layer
    """
    log_request()
    try:
        json_schema = {
            "type": "object",
            "required": ["published"],
            "properties": {
                "published": {"type": "boolean"},
                "geometry_precision": {"type": "integer"}
            },
        }
        
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)

        if project.exists():
            data = request.get_json()
            try:
                validate(data, json_schema)
            except ValidationError as e:
                return {"error": e.message}, 415
            
            published = data["published"]

            geometry_precision = 8 # default value in QGIS Server

            if "geometry_precision" in data:
                geometry_precision = data["geometry_precision"]
            
            project = QSAProject(name, psql_schema)

            rc, err = project.publish_wfs_layer(layer_name, published, geometry_precision)

            if err:
                return {"error": err}, 415
            return jsonify(rc), 201
        
        else:
            return {"error": "Project does not exist"}, 415
    
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415

@projects.post("/<name>/layers/<layer_name>/wms")
def project_publish_wms_layer(name, layer_name):
    """
    Change WMS publication status of an vector layer
    """
    log_request()
    try:
        json_schema = {
            "type": "object",
            "required": ["published"],
            "properties": {
                "published": {"type": "boolean"}
            },
        }
        
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)

        if project.exists():
            data = request.get_json()
            try:
                validate(data, json_schema)
            except ValidationError as e:
                return {"error": e.message}, 415
            
            published = data["published"]

            project = QSAProject(name, psql_schema)

            rc, err = project.publish_wms_layer(layer_name, published)

            if err:
                return {"error": err}, 415
            return jsonify(rc), 201
        
        else:
            return {"error": "Project does not exist"}, 415
    
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415
    
@projects.post("/<name>/layers/wms/feature-info")
def project_wms_adjust_feature_info(name):
    """
    Adjust the WMS Feature Info settings
    """ 
    log_request()
    try:
        json_schema = {
            "type": "object",
            "required": ["publish_geometry"],
            "properties": {
                "publish_geometry": {"type": "boolean"}
            },
        }
        
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)

        if project.exists():
            data = request.get_json()
            try:
                validate(data, json_schema)
            except ValidationError as e:
                return {"error": e.message}, 415
            
            publish_geometry = data["publish_geometry"]

            project = QSAProject(name, psql_schema)

            rc, err = project.wms_adjust_feature_info(publish_geometry)

            if err:
                return {"error": err}, 415
            return jsonify(rc), 201
        
        else:
            return {"error": "Project does not exist"}, 415
    
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415

@projects.delete("/<name>/layers/<layer_name>")
def project_del_layer(name, layer_name):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            if project.layer_exists(layer_name):
                rc = project.remove_layer(layer_name)
                return jsonify(rc), 201
            else:
                return {"error": "Layer does not exist"}, 415
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.get("/<name>/cache")
def project_cache(name):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            cache_infos, err = project.cache_metadata()
            if err:
                return {"error": err}, 415
            return jsonify(cache_infos), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415


@projects.post("/<name>/cache/reset")
def project_cache_reset(name):
    log_request()
    try:
        psql_schema = request.args.get("schema", default="public")
        project = QSAProject(name, psql_schema)
        if project.exists():
            rc, err = project.cache_reset()
            if err:
                return {"error": err}, 415
            return jsonify(rc), 201
        else:
            return {"error": "Project does not exist"}, 415
    except Exception as e:
        logger().exception(str(e))
        return {"error": "internal server error"}, 415
