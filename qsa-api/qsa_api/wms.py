# coding: utf8

from flask import current_app

from .project import QSAProject, StorageBackend


class WMS:
    @staticmethod
    def getmap_url(project, psql_schema, layer):
        p = QSAProject(project, psql_schema)
        props = p.layer(layer)

        bbox = props["bbox"].replace(" ", ",").replace(",,", ",").split(",")
        wms_bbox = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"

        return f"REQUEST=GetMap&WIDTH=400&HEIGHT=400&CRS={props['crs']}&VERSION=1.3.0&BBOX={wms_bbox}&LAYERS={layer}"

    @staticmethod
    def getmap(project, psql_schema, layer):
        base_url = f"{current_app.config['CONFIG'].qgisserver_url}"
        if QSAProject._storage_backend() == StorageBackend.FILESYSTEM:
            base_url = f"{base_url}/{project}?"
        elif QSAProject._storage_backend() == StorageBackend.POSTGRESQL:
            service = QSAProject._config().qgisserver_projects_psql_service
            base_url = f"{base_url}?MAP=postgresql:?service={service}%26schema={psql_schema}%26project={project}&"
        return f"{base_url}{WMS.getmap_url(project, psql_schema, layer)}"
