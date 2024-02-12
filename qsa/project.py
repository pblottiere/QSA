# coding: utf8

__contact__ = "info@hytech-imaging.fr"
__copyright__ = "Copyright (c) 2023 Hytech Imaging"

import shutil
from pathlib import Path
from flask import current_app

from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsSymbol,
    QgsProject,
    QgsMapLayer,
    QgsWkbTypes,
    QgsVectorLayer,
    QgsFeatureRenderer,
    QgsReadWriteContext,
    QgsSingleSymbolRenderer,
)
from qgis.PyQt.QtXml import QDomDocument, QDomNode

from .mapproxy import QSAMapProxy


RENDERER_TAG_NAME = "renderer-v2"  # constant from core/symbology/renderer.h


class QSAProject:
    def __init__(self, name: str) -> None:
        self.name: str = name

    @staticmethod
    def projects() -> list:
        p = []
        for i in QSAProject._qgis_projects_dir().glob("**/*.qgs"):
            p.append(QSAProject(i.parent.name))

        return p

    @property
    def styles(self) -> list[str]:
        s = []
        for qml in self._qgis_project_dir.glob("**/*.qml"):
            s.append(qml.stem)
        return s

    @property
    def project(self) -> QgsProject:
        project = QgsProject()
        project.read(self._qgis_project.as_posix())
        return project

    @property
    def layers(self) -> list:
        layers = []
        p = self.project
        for layer in p.mapLayers().values():
            layers.append(layer.name())
        return layers

    @property
    def metadata(self) -> dict:
        m = {}
        p = self.project
        m["author"] = p.metadata().author()
        m["creation_datetime"] = (
            p.metadata().creationDateTime().toString(Qt.ISODate)
        )
        m["crs"] = p.crs().authid()
        return m

    def style(self, name: str) -> dict:
        if name not in self.styles:
            return {}

        path = self._qgis_project_dir / f"{name}.qml"
        doc = QDomDocument()
        doc.setContent(open(path.as_posix()).read())
        node = QDomNode(doc.firstChild())

        renderer_node = node.firstChildElement(RENDERER_TAG_NAME)
        renderer = QgsFeatureRenderer.load(
            renderer_node, QgsReadWriteContext()
        )
        symbol = renderer.symbol()

        type = QgsSymbol.symbolTypeToString(symbol.type()).lower()

        m = {}
        m["name"] = name
        m["type"] = type
        m["width"] = symbol.width()
        m["color"] = symbol.color().name()

        return m

    def layer(self, name: str) -> dict:
        project = QgsProject()
        project.read(self._qgis_project.as_posix())
        layers = project.mapLayersByName(name)
        if layers:
            infos = {}
            infos["name"] = layers[0].name()
            infos["type"] = layers[0].type().name
            infos["source"] = layers[0].source()
            infos["crs"] = layers[0].crs().authid()
            infos["current_style"] = layers[0].styleManager().currentStyle()
            infos["styles"] = layers[0].styleManager().styles()
            infos["bbox"] = layers[0].extent().asWktCoordinates()
            return infos
        return {}

    def layer_update_style(
        self, layer_name: str, style_name: str, current: bool
    ) -> (bool, str):
        if layer_name not in self.layers:
            return False, f"Layer '{layer_name}' does not exist"

        if style_name != "default" and style_name not in self.styles:
            return False, f"Style '{style_name}' does not exist"

        project = QgsProject()
        project.read(self._qgis_project.as_posix())

        style_path = self._qgis_project_dir / f"{style_name}.qml"

        layer = project.mapLayersByName(layer_name)[0]

        if style_name not in layer.styleManager().styles():
            vl = QgsVectorLayer()
            rc = vl.loadNamedStyle(
                style_path.as_posix()
            )  # set "default" style

            rc = layer.styleManager().addStyle(
                style_name, vl.styleManager().style("default")
            )

        if current:
            rc = layer.styleManager().setCurrentStyle(style_name)

            mp = QSAMapProxy(self.name)
            mp.clear_cache(layer_name)

        project.write()

        return True, ""

    def layer_exists(self, name: str) -> bool:
        return bool(self.layer(name))

    def remove_layer(self, name: str) -> None:
        # remove layer in qgis project
        project = QgsProject()
        project.read(self._qgis_project.as_posix())

        ids = []
        for layer in project.mapLayersByName(name):
            ids.append(layer.id())
        project.removeMapLayers(ids)

        rc = project.write()

        # remove layer in mapproxy config
        mp = QSAMapProxy(self.name)
        mp.read()
        mp.remove_layer(name)
        mp.write()

        return rc

    def exists(self) -> bool:
        return self._qgis_project.exists()

    def create(self, author: str) -> None:
        if self.exists():
            return

        # create qgis project directory and .qgs
        self._qgis_project_dir.mkdir(parents=True, exist_ok=True)
        project = QgsProject()
        m = project.metadata()
        m.setAuthor(author)
        project.setMetadata(m)
        project.write(self._qgis_project.as_posix())

        # create mapproxy config file
        mp = QSAMapProxy(self.name)
        mp.create()

    def remove(self) -> None:
        shutil.rmtree(self._qgis_project_dir)
        QSAMapProxy(self.name).remove()

    def add_layer(self, datasource: str, name: str, epsg_code: int) -> bool:
        # add layer in qgis project
        vl = QgsVectorLayer(datasource, name, "ogr")
        crs = vl.crs()
        crs.createFromId(epsg_code)
        vl.setCrs(crs)

        project = QgsProject()
        project.read(self._qgis_project.as_posix())

        project.addMapLayer(vl)
        project.setCrs(crs)
        project.write()

        # add layer in mapproxy config file
        bbox = list(
            map(
                float,
                vl.extent().asWktCoordinates().replace(",", "").split(" "),
            )
        )

        mp = QSAMapProxy(self.name)
        mp.read()
        mp.add_layer(name, bbox, epsg_code)
        mp.write()

        return True

    def add_style(
        self,
        name: str,
        type: str,
        symbology: str,
        color: str,
        width: float,
        stroke_color: str,
        stroke_width: float,
    ) -> bool:
        r = None
        vl = QgsVectorLayer()

        if symbology == "single symbol" and type == "line":
            r = QgsSingleSymbolRenderer(
                QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            )
            r.symbol().setWidth(width)
            r.symbol().setColor(QColor(color))
        elif symbology == "single symbol" and type == "polygon":
            r = QgsSingleSymbolRenderer(
                QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
            )
            r.symbol().setColor(QColor(color))  # fill color

            r.symbol().symbolLayer(0).setStrokeColor(
                QColor(stroke_color)
            )
            r.symbol().symbolLayer(0).setStrokeWidth(
                stroke_width
            )

        if r:
            vl.setRenderer(r)

            path = self._qgis_project_dir / f"{name}.qml"
            vl.saveNamedStyle(
                path.as_posix(), categories=QgsMapLayer.Symbology
            )
            return True

        return False

    def remove_style(self, name: str) -> bool:
        if name not in self.styles:
            return False, f"Style '{name}' does not exist"

        p = self.project
        for layer in p.mapLayers().values():
            if name == layer.styleManager().currentStyle():
                return False, f"Style is used by {layer.name()}"

        for layer in p.mapLayers().values():
            layer.styleManager().removeStyle(name)

        path = self._qgis_project_dir / f"{name}.qml"
        path.unlink()

        p.write()

        return True

    @staticmethod
    def _qgis_projects_dir() -> Path:
        return current_app.config["CONFIG"].qgisserver_projects

    @property
    def _qgis_project_dir(self) -> Path:
        return QSAProject._qgis_projects_dir() / self.name

    @property
    def _qgis_project(self) -> Path:
        return self._qgis_project_dir / f"{self.name}.qgs"
