# coding: utf8

import sys
from pathlib import Path

from qgis.core import QgsRasterLayer, Qgis

from ..config import QSAConfig
from ..utils import logger, s3_parse_uri, s3_bucket_upload


class RasterOverview:
    def __init__(self, layer: QgsRasterLayer) -> None:
        self.layer = layer

    def is_valid(self):
        return self.layer.dataProvider().hasPyramids()

    def build(self) -> (bool, str):
        ds = self.layer.source()

        # check if rasters stored on S3
        if "/vsis3" not in ds:
            return False, "Building overviews is only supported for S3 rasters"

        # config overviews
        self.debug("Build external overviews")
        levels = self.layer.dataProvider().buildPyramidList()
        for idx, level in enumerate(levels):
            levels[idx].setBuild(True)

        # build overviews
        fmt = Qgis.RasterPyramidFormat.GeoTiff
        err = self.layer.dataProvider().buildPyramids(levels, "NEAREST", fmt)
        if err:
            return False, f"Cannot build overview ({err})"

        # search ovr file in GDAL PAM directory
        ovrfile = f"{Path(ds).name}.ovr"
        ovrpath = next(
            QSAConfig().gdal_pam_proxy_dir.glob(f"*{ovrfile}"), None
        )
        if not ovrpath:
            return False, "Cannot find OVR file in GDAL_PAM_PROXY_DIR"

        # upload
        bucket, subdirs, _ = s3_parse_uri(ds)
        dest = Path(subdirs) / ovrfile

        rc, msg = s3_bucket_upload(bucket, ovrpath.as_posix(), dest.as_posix())
        if not rc:
            return False, msg

        # clean
        self.debug("Remove ovr file in GDAL PAM directory")
        ovrpath.unlink()

        return True, ""

    def debug(self, msg) -> None:
        caller = f"{self.__class__.__name__}.{sys._getframe().f_back.f_code.co_name}"
        msg = f"[{caller}] {msg}"
        logger().debug(msg)
