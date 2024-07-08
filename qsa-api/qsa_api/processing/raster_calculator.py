# coding: utf8

import sys
import rasterio
import tempfile
from pathlib import Path
from multiprocessing import Process, Manager

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

    def process(self, out_uri: str) -> (bool, str):
        # Some kind of cache is bothering us because when a raster layer is
        # added on S3, we cannot open it with GDAL provider later. The
        # QgsApplication needs to be restarted... why???
        manager = Manager()
        out = manager.dict()

        p = Process(target=RasterCalculator._process, args=(self.project_uri, self.expression, out_uri, out))
        p.start()
        p.join()

        return out["rc"], out["error"]

    @staticmethod
    def _process(expression: str, project_uri: str, out_uri: str, out: dict) -> None:
        vuri = RasterCalculator._virtual_uri(project_uri, expression)
        lyr = QgsRasterLayer(vuri, "", "virtualraster")

        with tempfile.NamedTemporaryFile(suffix='.tif') as fp:
            RasterCalculator._debug("Write temporary raster on disk")

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
                out["rc"] = False
                out["error"] = "Failed to write raster"
                return

            # update nodata
            RasterCalculator._update_nodata(fp.name)

            # upload
            bucket, subdirs, filename = s3_parse_uri(out_uri)
            dest = Path(subdirs) / Path(filename)
            rc, msg = s3_bucket_upload(bucket, fp.name, dest.as_posix())
            if not rc:
                out["rc"] = False
                out["error"] = msg
                return

            # build overview
            lyr = QgsRasterLayer(fp.name, "", "gdal")
            RasterCalculator._debug("Build overview")
            fmt = Qgis.RasterPyramidFormat.GeoTiff
            levels = lyr.dataProvider().buildPyramidList()
            for idx, level in enumerate(levels):
                levels[idx].setBuild(True)
            err = lyr.dataProvider().buildPyramids(levels, "NEAREST", fmt)
            if err:
                out["rc"] = False
                out["error"] = f"Cannot build overview ({err})"
                return

            # upload overview
            ovr = f"{fp.name}.ovr"
            dest = f"{dest.as_posix()}.ovr"
            rc, msg = s3_bucket_upload(bucket, ovr, dest)
            if not rc:
                out["rc"] = False
                out["error"] = msg
                return

            out["rc"] = True
            out["error"] = ""

    @staticmethod
    def _update_nodata(filename: str) -> None:
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
                RasterCalculator._debug(f"Set no data value to {stats.minimumValue}")
                with rasterio.open(filename, "r+") as dataset:
                    dataset.nodata = stats.minimumValue
                break

    @staticmethod
    def _virtual_uri(project_uri: str, expression: str) -> str:
        params = QgsRasterDataProvider.VirtualRasterParameters()
        params.formula = expression
        params.crs = QgsCoordinateReferenceSystem("EPSG:3857")

        project = QgsProject.instance()
        project.read(project_uri)

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

            if layer.name() not in expression:
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

    @staticmethod
    def _debug(msg: str) -> None:
        caller = "raster_calculator"
        msg = f"[{caller}] {msg}"
        logger().debug(msg)

    def is_valid(self) -> bool:
        node = QgsRasterCalcNode.parseRasterCalcString(self.expression, "")
        if node is None:
            return False
        return True
