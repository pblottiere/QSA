# coding: utf8

from .project import QSAProject


class WMS:
    @staticmethod
    def getmap(project, layer):
        p = QSAProject(project)
        props = p.layer(layer)

        bbox = props["bbox"].replace(" ", ",").replace(",,", ",").split(",")
        wms_bbox = f"{bbox[1]},{bbox[0]},{bbox[3]},{bbox[2]}"

        return f"REQUEST=GetMap&WIDTH=400&HEIGHT=400&CRS={props['crs']}&VERSION=1.3.0&BBOX={wms_bbox}&LAYERS={layer}"
