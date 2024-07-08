# coding: utf8

import sys
import rasterio
import tempfile
from pathlib import Path

from qgis.PyQt.QtCore import QUrl, QUrlQuery
from qgis.analysis import QgsRasterCalcNode
from qgis.core import (
    Qgis,
    QgsProject,
    QgsMapLayer,
    QgsRasterPipe,
    QgsRasterLayer,
    QgsRasterBandStats,
    QgsRasterFileWriter,
    QgsRasterDataProvider,
    QgsContrastEnhancement,
    QgsCoordinateTransform,
    QgsCoordinateReferenceSystem,
)

from ..utils import s3_bucket_upload, s3_parse_uri, logger


class RasterCalculator:
    def __init__(self, project_uri: str, expression: str) -> None:
        self.expression = expression
        self.project_uri = project_uri

    def virtual_uri(self) -> str:
        params = QgsRasterDataProvider.VirtualRasterParameters()
        params.formula = self.expression
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

            if layer.dataProvider().name() == "virtualraster":
                continue

            if layer.name() in lyr_names:
                continue

            if layer.name() not in self.expression:
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

            # rInputLayers cannot be set from Python :(
            # hack based on QgsRasterDataProvider.encodeVirtualRasterProviderUri
            if vlayer.name not in lyr_names:
                params_query.addQueryItem(vlayer.name + ":uri", vlayer.uri)
                params_query.addQueryItem(
                    vlayer.name + ":provider", vlayer.provider
                )

            lyr_names.append(layer.name())

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

    def process(self, out_uri: str) -> (bool, str):
        vuri = self.virtual_uri()
        lyr = QgsRasterLayer(vuri, "", "virtualraster")

        rc = False
        msg = ""

        with tempfile.NamedTemporaryFile(suffix='.tif') as fp:
            self.debug("Write temporary raster on disk")

            file_writer = QgsRasterFileWriter(fp.name)
            pipe = QgsRasterPipe()
            pipe.set(lyr.dataProvider().clone())
            rc = file_writer.writeRaster(
                pipe,
                lyr.width(),
                lyr.height(),
                lyr.extent(),
                lyr.crs(),
            )
            if rc != Qgis.RasterFileWriterResult.Success:
                return False, "Failed to write raster"

            # update nodata
            self.update_nodata(fp.name)

            # upload
            bucket, subdirs, filename = s3_parse_uri(out_uri)
            dest = Path(subdirs) / Path(filename)
            rc, msg = s3_bucket_upload(bucket, fp.name, dest.as_posix())
            if not rc:
                return False, msg

            # build overview
            lyr = QgsRasterLayer(fp.name, "", "gdal")
            self.debug("Build overview")
            fmt = Qgis.RasterPyramidFormat.GeoTiff
            levels = lyr.dataProvider().buildPyramidList()
            for idx, level in enumerate(levels):
                levels[idx].setBuild(True)
            err = lyr.dataProvider().buildPyramids(levels, "NEAREST", fmt)
            if err:
                return False, f"Cannot build overview ({err})"

            # upload overview
            ovr = f"{fp.name}.ovr"
            dest = f"{dest.as_posix()}.ovr"
            rc, msg = s3_bucket_upload(bucket, ovr, dest)
            if not rc:
                return False, msg

        return rc, msg

    def is_valid(self) -> bool:
        node = QgsRasterCalcNode.parseRasterCalcString(self.expression, "")
        if node is None:
            return False
        return True

    def update_nodata(self, filename):
        # check if min is minimumValuePossible for the corresponding type
        # if yes, update noDataValue
        lyr = QgsRasterLayer(filename, "", "gdal")
        stats = lyr.dataProvider().bandStatistics(
            1,
            QgsRasterBandStats.Min | QgsRasterBandStats.Max,
            lyr.extent(),
            250000,
        )

        for t in Qgis.DataType:
            if (
                stats.minimumValue
                == QgsContrastEnhancement.minimumValuePossible(t)
            ):
                self.debug(f"Set no data value to {stats.minimumValue}")
                with rasterio.open(filename, "r+") as dataset:
                    dataset.nodata = stats.minimumValue
                break

    def debug(self, msg) -> None:
        caller = f"{self.__class__.__name__}.{sys._getframe().f_back.f_code.co_name}"
        msg = f"[{caller}] {msg}"
        logger().debug(msg)
