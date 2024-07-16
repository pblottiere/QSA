# coding: utf8

from .project import QSAProject
from .utils import qgisserver_base_url


class WMS:
    @staticmethod
    def getmap_url(project, psql_schema, layer):
        p = QSAProject(project, psql_schema)
        props = p.layer(layer)

        if "bbox" not in props:
            return "Invalid layer"

        bbox = props["bbox"].replace(" ", ",").replace(",,", ",").split(",")
        wms_bbox = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"

        return f"REQUEST=GetMap&WIDTH=400&HEIGHT=400&CRS={props['crs']}&VERSION=1.3.0&BBOX={wms_bbox}&LAYERS={layer}"

    @staticmethod
    def getmap(project, psql_schema, layer):
        return f"{qgisserver_base_url(project, psql_schema)}{WMS.getmap_url(project, psql_schema, layer)}"
