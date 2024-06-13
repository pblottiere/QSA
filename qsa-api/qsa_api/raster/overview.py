# coding: utf8

import boto3
from pathlib import Path

from qgis.core import QgsRasterLayer, Qgis

from ..config import QSAConfig


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
            return False, f"Cannot find OVR file in GDAL_PAM_PROXY_DIR"

        # upload : not robust enough :/
        bucket = ds.split("/")[2]
        subdir = Path(ds.split(f"/vsis3/{bucket}/")[1]).parent
        s3 = boto3.resource("s3")
        s3.Bucket(bucket).upload_file(
            ovrpath.as_posix(), (subdir / ovrfile).as_posix()
        )

        # clean
        ovrpath.unlink()

        return True, ""
