# coding: utf8

import os
import sys
import boto3
import logging
import threading
from pathlib import Path
from botocore.exceptions import ClientError

from qgis.core import QgsRasterLayer, Qgis

from ..utils import logger
from ..config import QSAConfig


# see boto3 doc
class ProgressPercentage:

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._last = 0

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100

            if percentage < self._last + 10:
                return

            self._last = percentage

            if QSAConfig().loglevel == logging.DEBUG:
                print(
                    "\r%s  %s / %s  (%.2f%%)"
                    % (
                        self._filename,
                        self._seen_so_far,
                        self._size,
                        percentage,
                    ),
                    file=sys.stderr,
                )
            sys.stdout.flush()


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
            return False, f"Cannot find OVR file in GDAL_PAM_PROXY_DIR"

        # upload : not robust enough :/
        size = float(os.path.getsize(ovrpath.as_posix()) >> 20)
        bucket = ds.split("/")[2]
        subdir = Path(ds.split(f"/vsis3/{bucket}/")[1]).parent
        dest = (subdir / ovrfile).as_posix()
        self.debug(f"Upload {dest} ({size}MB) to S3 bucket")

        try:
            s3 = boto3.resource("s3")
            s3.Bucket(bucket).upload_file(
                ovrpath.as_posix(),
                dest,
                Callback=ProgressPercentage(ovrpath.as_posix()),
            )
        except ClientError as e:
            return False, "Upload to S3 bucket failed"

        # clean
        self.debug("Remove ovr file in GDAL PAM directory")
        ovrpath.unlink()

        return True, ""

    def debug(self, msg) -> None:
        caller = f"{self.__class__.__name__}.{sys._getframe().f_back.f_code.co_name}"
        msg = f"[{caller}] {msg}"
        logger().debug(msg)
