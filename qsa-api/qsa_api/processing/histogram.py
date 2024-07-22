# coding: utf8

from multiprocessing import Process, Manager

from qgis.core import QgsProject, QgsRectangle


class Histogram:
    def __init__(self, project_uri: str, layer: str) -> None:
        self.layer = layer
        self.project_uri = project_uri

    def process(self, mini, maxi, count) -> (bool, dict):
        # Some kind of cache is bothering us because when a raster layer is
        # added on S3, we cannot open it with GDAL provider later. The
        # QgsApplication needs to be restarted... why???
        manager = Manager()
        out = manager.dict()

        p = Process(
            target=Histogram._process,
            args=(self.project_uri, self.layer, mini, maxi, count, out),
        )
        p.start()
        p.join()

        if "histo" in out:
            return out["histo"].copy()

        return {}

    @staticmethod
    def _process(project_uri: str, layer: str, mini, maxi, count, out: dict) -> None:

        project = QgsProject.instance()
        project.read(project_uri)
        lyr = project.mapLayersByName(layer)[0]

        histo = {}
        for band in range(lyr.bandCount()):
            h = (
                lyr.dataProvider()
                .histogram(band + 1, count, mini, maxi, QgsRectangle(), 250000)
            )

            histo[band + 1] = {}
            histo[band + 1]["min"] = h.minimum
            histo[band + 1]["max"] = h.maximum
            histo[band + 1]["values"] = h.histogramVector

        out["histo"] = histo
