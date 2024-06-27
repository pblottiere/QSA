# coding: utf8

import sys

from qgis.PyQt.QtCore import QUrl, QUrlQuery
from qgis.analysis import QgsRasterCalcNode
from qgis.core import (
    QgsRasterDataProvider,
    QgsProject,
    QgsMapLayer,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
)


class RasterCalculator:
    def __init__(self, project_uri: str, datasource: str, name: str) -> None:
        self.name = name
        self.datasource = datasource
        self.project_uri = project_uri

    def virtual_uri(self) -> str:
        params = QgsRasterDataProvider.VirtualRasterParameters()
        params.formula = self.datasource
        params.crs = QgsCoordinateReferenceSystem("EPSG:3857")

        project = QgsProject.instance()
        project.read(self.project_uri)

        lyr_names = []
        extent = None
        width = 0
        height = 0

        params_query = QUrlQuery()
        for layer in project.mapLayers().values():
            if layer.type() != QgsMapLayer.RasterLayer:
                continue

            if layer.name in lyr_names:
                continue

            transform = QgsCoordinateTransform(
                layer.crs(), params.crs, project
            )
            lyr_extent = transform.transformBoundingBox(layer.extent())

            if extent is None:
                extent = lyr_extent
            else:
                extent.combineExtentWith(lyr_extent)

            if layer.width() > width:
                width = layer.width()

            if layer.height() > height:
                height = layer.height()

            vlayer = QgsRasterDataProvider.VirtualRasterInputLayers()
            vlayer.name = layer.name()
            vlayer.provider = layer.dataProvider().name()
            vlayer.uri = layer.source()

            lyr_names.append(layer.name())

            # rInputLayers cannot be set from Python :(
            # hack based on QgsRasterDataProvider.encodeVirtualRasterProviderUri
            params_query.addQueryItem(vlayer.name + ":uri", vlayer.uri)
            params_query.addQueryItem(
                vlayer.name + ":provider", vlayer.provider
            )

        params.width = width
        params.height = height
        params.extent = extent

        vuri = QgsRasterDataProvider.encodeVirtualRasterProviderUri(params)

        # rInputLayers cannot be set from Python :(
        # hack based on QgsRasterDataProvider.encodeVirtualRasterProviderUri
        params_uri = QUrl()
        params_uri.setQuery(params_query)
        params_vuri = str(
            QUrl.toPercentEncoding(
                str(params_uri.toEncoded(), encoding="utf-8")
            ),
            encoding="utf-8",
        )[3:]

        return f"{vuri}%26{params_vuri}"

    def is_valid(self) -> bool:
        node = QgsRasterCalcNode.parseRasterCalcString(self.datasource, "")
        if node is None:
            return False
        return True
