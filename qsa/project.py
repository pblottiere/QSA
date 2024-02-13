# coding: utf8

import shutil
import sqlite3
from pathlib import Path
from flask import current_app

from qgis.PyQt.QtCore import Qt
from qgis.core import (
    QgsSymbol,
    QgsProject,
    QgsMapLayer,
    QgsWkbTypes,
    QgsFillSymbol,
    QgsLineSymbol,
    QgsVectorLayer,
    QgsFeatureRenderer,
    QgsReadWriteContext,
    QgsSingleSymbolRenderer,
    QgsSimpleFillSymbolLayer,
    QgsSimpleLineSymbolLayer,
)
from qgis.PyQt.QtXml import QDomDocument, QDomNode

from .mapproxy import QSAMapProxy


RENDERER_TAG_NAME = "renderer-v2"  # constant from core/symbology/renderer.h


class QSAProject:
    def __init__(self, name: str) -> None:
        self.name: str = name

    @property
    def sqlite_db(self) -> Path:
        p = QSAProject._qgis_projects_dir() / "qsa.db"
        if not p.exists():
            con = sqlite3.connect(p)
            cur = con.cursor()
            cur.execute(
                "CREATE TABLE styles_default(geometry, symbology, symbol, style)"
            )
            cur.execute(
                "INSERT INTO styles_default VALUES('line', 'single_symbol', 'line', 'default')"
            )
            cur.execute(
                "INSERT INTO styles_default VALUES('polygon', 'single_symbol', 'fill', 'default')"
            )
            con.commit()
            con.close()
        return p

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

    def style_default(self, symbol: str) -> bool:
        con = sqlite3.connect(self.sqlite_db.as_posix())
        cur = con.cursor()
        sql = f"SELECT style FROM styles_default WHERE symbol = '{symbol}'"
        res = cur.execute(sql)
        default_style = res.fetchone()[0]
        con.close()
        return default_style

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
        props = symbol.symbolLayer(0).properties()

        geom = "line"
        symbol = QgsSymbol.symbolTypeToString(symbol.type()).lower()
        if symbol == "fill":
            geom = "polygon"

        m = {}
        m["symbology"] = "single_symbol"
        m["name"] = name
        m["symbol"] = symbol
        m["geometry"] = geom
        m["properties"] = props

        return m

    def default_style_for_symbol(self, symbol: str) -> str:
        con = sqlite3.connect(self.sqlite_db.as_posix())
        cur = con.cursor()
        res = cur.execute(
            f"SELECT style FROM styles_default WHERE symbol = '{symbol}'"
        )
        s = res.fetchone()[0]
        con.close()
        return s

    def style_update(
        self, geometry: str, symbology: str, symbol: str, style: str
    ) -> None:
        con = sqlite3.connect(self.sqlite_db.as_posix())
        cur = con.cursor()
        sql = f"UPDATE styles_default SET style = '{style}' WHERE symbol = '{symbol}'"
        cur.execute(sql)
        con.commit()
        con.close()

    def default_styles(self) -> list:
        s = {}

        s["polygon"] = {"single_symbol": {}}
        s["line"] = {"single_symbol": {}}

        s["polygon"]["single_symbol"]["fill"] = self.default_style_for_symbol(
            "fill"
        )
        s["line"]["single_symbol"]["line"] = self.default_style_for_symbol(
            "line"
        )

        return s

    def layer(self, name: str) -> dict:
        project = QgsProject()
        project.read(self._qgis_project.as_posix())
        layers = project.mapLayersByName(name)
        if layers:
            layer = layers[0]

            infos = {}
            infos["valid"] = layer.isValid()
            infos["name"] = layer.name()
            infos["type"] = layer.type().name.lower()
            infos["geometry"] = QgsWkbTypes.displayString(layer.wkbType())
            infos["source"] = layer.source()
            infos["crs"] = layer.crs().authid()
            infos["current_style"] = layer.styleManager().currentStyle()
            infos["styles"] = layer.styleManager().styles()
            infos["bbox"] = layer.extent().asWktCoordinates()
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
            vl.loadNamedStyle(style_path.as_posix())  # set "default" style

            layer.styleManager().addStyle(
                style_name, vl.styleManager().style("default")
            )

        if current:
            layer.styleManager().setCurrentStyle(style_name)
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

        if not vl.isValid():
            return False

        # create project
        project = QgsProject()
        project.read(self._qgis_project.as_posix())

        project.addMapLayer(vl)
        project.setCrs(crs)
        project.write()

        # set default style
        geometry = vl.geometryType().name.lower()
        symbol = "line"
        if geometry == "polygon":
            symbol = "fill"
        default_style = self.style_default(symbol)

        self.layer_update_style(name, default_style, True)

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
        symbol: str,
        symbology: str,
        properties: dict,
    ) -> bool:
        r = None
        vl = QgsVectorLayer()

        if symbology != "single_symbol":
            return False

        if symbol == "line":
            r = QgsSingleSymbolRenderer(
                QgsSymbol.defaultSymbol(QgsWkbTypes.LineGeometry)
            )

            props = QgsSimpleLineSymbolLayer().properties()
            for key in properties.keys():
                if key not in props:
                    return False

            symbol = QgsLineSymbol.createSimple(properties)
            r.setSymbol(symbol)
        elif symbol == "fill":
            r = QgsSingleSymbolRenderer(
                QgsSymbol.defaultSymbol(QgsWkbTypes.PolygonGeometry)
            )

            props = QgsSimpleFillSymbolLayer().properties()
            for key in properties.keys():
                if key not in props:
                    return False

            symbol = QgsFillSymbol.createSimple(properties)
            r.setSymbol(symbol)

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
