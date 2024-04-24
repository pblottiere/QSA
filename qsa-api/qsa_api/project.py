# coding: utf8

import shutil
import sqlite3
from enum import Enum
from pathlib import Path
from flask import current_app

from qgis.PyQt.QtCore import Qt, QUrl, QUrlQuery
from qgis.core import (
    Qgis,
    QgsSymbol,
    QgsProject,
    QgsMapLayer,
    QgsWkbTypes,
    QgsFillSymbol,
    QgsLineSymbol,
    QgsApplication,
    QgsVectorLayer,
    QgsRasterLayer,
    QgsMarkerSymbol,
    QgsFeatureRenderer,
    QgsReadWriteContext,
    QgsSingleSymbolRenderer,
    QgsSimpleFillSymbolLayer,
    QgsSimpleLineSymbolLayer,
    QgsSimpleMarkerSymbolLayer,
)
from qgis.PyQt.QtXml import QDomDocument, QDomNode

from .mapproxy import QSAMapProxy


RENDERER_TAG_NAME = "renderer-v2"  # constant from core/symbology/renderer.h


class StorageBackend(Enum):
    INVALID = 0
    FILESYSTEM = 1
    POSTGRESQL = 2

    def from_str(storage: str) -> "StorageBackend":
        if storage.lower() == StorageBackend.FILESYSTEM.name.lower():
            return StorageBackend.FILESYSTEM
        elif storage.lower() == StorageBackend.FILESYSTEM.name.lower():
            return StorageBackend.POSTGRESQL
        return INVALID


class QSAProject:
    def __init__(self, name: str, schema: str = "public") -> None:
        self.name: str = name
        self.schema: str = "public"
        if schema:
            self.schema = schema

    @property
    def sqlite_db(self) -> Path:
        p = self._qgis_project_dir / "qsa.db"
        if not p.exists():
            con = sqlite3.connect(p)
            cur = con.cursor()
            cur.execute("CREATE TABLE styles_default(geometry, style)")
            cur.execute("INSERT INTO styles_default VALUES('line', 'default')")
            cur.execute(
                "INSERT INTO styles_default VALUES('polygon', 'default')"
            )
            cur.execute(
                "INSERT INTO styles_default VALUES('point', 'default')"
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
        project.read(self._qgis_project_uri)
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

    def style_default(self, geometry: str) -> bool:
        con = sqlite3.connect(self.sqlite_db.as_posix())
        cur = con.cursor()
        sql = f"SELECT style FROM styles_default WHERE geometry = '{geometry}'"
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

    def style_update(self, geometry: str, style: str) -> None:
        con = sqlite3.connect(self.sqlite_db.as_posix())
        cur = con.cursor()
        sql = f"UPDATE styles_default SET style = '{style}' WHERE geometry = '{geometry}'"
        cur.execute(sql)
        con.commit()
        con.close()

    def default_styles(self) -> list:
        s = {}

        s["polygon"] = self.style_default("polygon")
        s["line"] = self.style_default("line")
        s["point"] = self.style_default("point")

        return s

    def layer(self, name: str) -> dict:
        project = QgsProject()
        project.read(self._qgis_project_uri)
        layers = project.mapLayersByName(name)
        if layers:
            layer = layers[0]

            infos = {}
            infos["valid"] = layer.isValid()
            infos["name"] = layer.name()
            infos["type"] = layer.type().name.lower()

            if layer.type() == Qgis.LayerType.Vector:
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
        project.read(self._qgis_project_uri)

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

            if self._mapproxy_enabled:
                mp = QSAMapProxy(self.name)
                mp.clear_cache(layer_name)

        project.write()

        return True, ""

    def layer_exists(self, name: str) -> bool:
        return bool(self.layer(name))

    def remove_layer(self, name: str) -> None:
        # remove layer in qgis project
        project = QgsProject()
        project.read(self._qgis_project_uri)

        ids = []
        for layer in project.mapLayersByName(name):
            ids.append(layer.id())
        project.removeMapLayers(ids)

        rc = project.write()

        # remove layer in mapproxy config
        if self._mapproxy_enabled:
            mp = QSAMapProxy(self.name)
            mp.read()
            mp.remove_layer(name)
            mp.write()

        return rc

    def exists(self) -> bool:
        if self._storage_backend == StorageBackend.FILESYSTEM:
            return self._qgis_project_dir.exists()
        else:
            service = QSAProject._config().qgisserver_projects_psql_service
            uri = f"postgresql:?service={service}&schema={self.schema}"

            storage = QgsApplication.instance().projectStorageRegistry().projectStorageFromType("postgresql")
            projects = storage.listProjects(uri)

            return self.name in projects and self._qgis_projects_dir.exists()

    def create(self, author: str) -> bool:
        if self.exists():
            return False

        # create qgis directory for qsa sqlite database and .qgs file if
        # filesystem storage based
        self._qgis_project_dir.mkdir(parents=True, exist_ok=True)

        # create qgis project
        project = QgsProject()
        m = project.metadata()
        m.setAuthor(author)
        project.setMetadata(m)
        rc = project.write(self._qgis_project_uri)

        print(rc)
        print(self._qgis_project_uri)

        # create mapproxy config file
        if self._mapproxy_enabled:
            mp = QSAMapProxy(self.name)
            mp.create()

        return rc

    def remove(self) -> None:
        shutil.rmtree(self._qgis_project_dir)

        if self._storage_backend == StorageBackend.POSTGRESQL:
            storage = QgsApplication.projectStorageRegistry().projectStorageFromUri(self.name)
            storage.removeProject(uri)

        if self._mapproxy_enabled:
            QSAMapProxy(self.name).remove()

    def add_layer(
        self, datasource: str, layer_type: str, name: str, epsg_code: int
    ) -> (bool, str):
        t = self._layer_type(layer_type)
        if t is None:
            return False, "Invalid layer type"

        lyr = None
        if t == Qgis.LayerType.Vector:
            lyr = QgsVectorLayer(datasource, name, "ogr")
        elif t == Qgis.LayerType.Raster:
            lyr = QgsRasterLayer(datasource, name, "gdal")
        else:
            return False, "Invalid layer type"

        crs = lyr.crs()
        crs.createFromString(f"EPSG:{epsg_code}")
        lyr.setCrs(crs)

        if not lyr.isValid():
            return False, "Invalid layer"

        # create project
        project = QgsProject()
        project.read(self._qgis_project_uri)

        project.addMapLayer(lyr)
        project.setCrs(crs)
        project.write()

        # set default style
        if t == Qgis.LayerType.Vector:
            geometry = lyr.geometryType().name.lower()
            default_style = self.style_default(geometry)

            self.layer_update_style(name, default_style, True)

        # add layer in mapproxy config file
        bbox = list(
            map(
                float,
                lyr.extent().asWktCoordinates().replace(",", "").split(" "),
            )
        )

        if self._mapproxy_enabled:
            mp = QSAMapProxy(self.name)
            mp.read()
            mp.add_layer(name, bbox, epsg_code)
            mp.write()

        return True, ""

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
        elif symbol == "marker":
            r = QgsSingleSymbolRenderer(
                QgsSymbol.defaultSymbol(QgsWkbTypes.PointGeometry)
            )

            props = QgsSimpleMarkerSymbolLayer().properties()
            for key in properties.keys():
                if key not in props:
                    return False

            symbol = QgsMarkerSymbol.createSimple(properties)
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
        return Path(QSAProject._config().qgisserver_projects_dir)

    @staticmethod
    def _layer_type(layer_type: str) -> Qgis.LayerType | None:
        if layer_type.lower() == "vector":
            return Qgis.LayerType.Vector
        elif layer_type.lower() == "raster":
            return Qgis.LayerType.Raster
        return None

    @staticmethod
    def _config():
        return current_app.config["CONFIG"]

    @property
    def _mapproxy_enabled(self) -> bool:
        return bool(self._config().mapproxy_projects_dir)

    @property
    def _qgis_project_dir(self) -> Path:
        return self._qgis_projects_dir() / self.name

    @property
    def _qgis_project_uri(self) -> str:
        if self._storage_backend == StorageBackend.POSTGRESQL:
            service = QSAProject._config().qgisserver_projects_psql_service
            return f"postgresql:?service={service}&schema={self.schema}&project={self.name}"
        else:
            return (self._qgis_project_dir / f"{self.name}.qgs").as_posix()

    @property
    def _storage_backend(self) -> StorageBackend:
        if self._config().qgisserver_projects_psql_service:
            return StorageBackend.POSTGRESQL
        return StorageBackend.FILESYSTEM
