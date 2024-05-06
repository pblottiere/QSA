# coding: utf8

from enum import Enum
from flask import current_app

from qgis.core import (
    QgsRasterMinMaxOrigin,
    QgsContrastEnhancement,
    QgsSingleBandGrayRenderer,
    QgsMultiBandColorRenderer,
)


def config():
    return current_app.config["CONFIG"]


class StorageBackend(Enum):
    FILESYSTEM = 0
    POSTGRESQL = 1

    @staticmethod
    def type() -> "StorageBackend":
        if config().qgisserver_projects_psql_service:
            return StorageBackend.POSTGRESQL
        return StorageBackend.FILESYSTEM


def qgisserver_base_url(project: str, psql_schema: str) -> str:
    url = f"{config().qgisserver_url}"
    if StorageBackend.type() == StorageBackend.FILESYSTEM:
        url = f"{url}/{project}?"
    elif StorageBackend.type() == StorageBackend.POSTGRESQL:
        service = config().qgisserver_projects_psql_service
        url = f"{url}?MAP=postgresql:?service={service}%26schema={psql_schema}%26project={project}&"
    return url


class RasterSymbologyRenderer:
    class Type(Enum):
        SINGLE_BAND_GRAY = QgsSingleBandGrayRenderer(None, 1).type()
        MULTI_BAND_COLOR = QgsMultiBandColorRenderer(None, 1, 1, 1).type()

    def __init__(self, name: str) -> None:
        self.renderer = None
        self.contrast_algorithm = None
        self.contrast_limits = QgsRasterMinMaxOrigin.Limits.MinMax

        if name == RasterSymbologyRenderer.Type.SINGLE_BAND_GRAY.value:
            self.renderer = QgsSingleBandGrayRenderer(None, 1)
        elif name == RasterSymbologyRenderer.Type.MULTI_BAND_COLOR.value:
            self.renderer = QgsMultiBandColorRenderer(None, 1, 1, 1)

    @property
    def type(self):
        if (
            self.renderer.type()
            == RasterSymbologyRenderer.Type.SINGLE_BAND_GRAY.value
        ):
            return RasterSymbologyRenderer.Type.SINGLE_BAND_GRAY
        elif (
            self.renderer.type()
            == RasterSymbologyRenderer.Type.MULTI_BAND_COLOR.value
        ):
            return RasterSymbologyRenderer.Type.MULTI_BAND_COLOR

        return None

    def load(self, properties: dict) -> (bool, str):
        if not self.renderer:
            return False, "Invalid renderer"

        if "contrast_enhancement" in properties:
            self._load_contrast_enhancement(properties["contrast_enhancement"])

        if (
            self.renderer.type()
            == RasterSymbologyRenderer.Type.MULTI_BAND_COLOR
        ):
            self._load_multibandcolor_properties(properties)
        elif (
            self.renderer.type()
            == RasterSymbologyRenderer.Type.SINGLE_BAND_GRAY
        ):
            self._load_singlebandgray_properties(properties)

        return True, ""

    def _load_multibandcolor_properties(self, properties: dict) -> None:
        if "red" in properties:
            red = properties["red"]
            self.renderer.setRedBand(int(red["band"]))

        if "blue" in properties:
            blue = properties["blue"]
            self.renderer.setBlueBand(int(blue["band"]))

        if "green" in properties:
            green = properties["green"]
            self.renderer.setGreenBand(int(green["band"]))

    def _load_singlebandgray_properties(self, properties: dict) -> None:
        if "gray_band" in properties:
            band = properties["gray_band"]
            self.renderer.setGrayBand(int(band))

        if "color_gradient" in properties:
            gradient = properties["color_gradient"]
            if gradient == "blacktowhite":
                self.renderer.setGradient(
                    QgsSingleBandGrayRenderer.Gradient.BlackToWhite
                )
            elif gradient == "whitetoblack":
                self.renderer.setGradient(
                    QgsSingleBandGrayRenderer.Gradient.WhiteToBlack
                )

    def _load_contrast_enhancement(self, properties: dict) -> None:
        alg = properties["algorithm"]
        if alg == "StretchToMinimumMaximum":
            self.contrast_algorithm = (
                QgsContrastEnhancement.ContrastEnhancementAlgorithm.StretchToMinimumMaximum
            )
        elif alg == "NoEnhancement":
            self.contrast_algorithm = (
                QgsContrastEnhancement.ContrastEnhancementAlgorithm.NoEnhancement
            )
        elif alg == "StretchAndClipToMinimumMaximum":
            self.contrast_algorithm = (
                QgsContrastEnhancement.ContrastEnhancementAlgorithm.StretchAndClipToMinimumMaximum
            )
        elif alg == "ClipToMinimumMaximum":
            self.contrast_algorithm = (
                QgsContrastEnhancement.ContrastEnhancementAlgorithm.ClipToMinimumMaximum
            )

        limits = properties["limits_min_max"]
        if limits == "UserDefined":
            self.contrast_limits = QgsRasterMinMaxOrigin.Limits.None_
        elif limits == "MinMax":
            self.contrast_limits = QgsRasterMinMaxOrigin.Limits.MinMax
        elif limits == "StdDev":
            self.contrast_limits = QgsRasterMinMaxOrigin.Limits.StdDev
        elif limits == "CumulativeCut":
            self.contrast_limits = QgsRasterMinMaxOrigin.Limits.CumulativeCut
