# coding: utf8

from multiprocessing import Process, Manager

from qgis.core import QgsProject, QgsRectangle


class Histogram:
    def __init__(self, project_uri: str, layer: str) -> None:
        self.layer = layer
        self.project_uri = project_uri

    def process(self) -> (bool, dict):
        # Some kind of cache is bothering us because when a raster layer is
        # added on S3, we cannot open it with GDAL provider later. The
        # QgsApplication needs to be restarted... why???
        manager = Manager()
        out = manager.dict()

        p = Process(
            target=Histogram._process,
            args=(self.project_uri, self.layer, out),
        )
        p.start()
        p.join()

        if "histo" in out:
            return out["histo"]

        return {}

    @staticmethod
    def _process(project_uri: str, layer: str, out: dict) -> None:

        project = QgsProject.instance()
        project.read(project_uri)
        lyr = project.mapLayersByName(layer)[0]

        histo = {}
        for band in range(lyr.bandCount()):
            histo[band + 1] = (
                lyr.dataProvider()
                .histogram(band + 1, 1000, None, None, QgsRectangle(), 250000)
                .histogramVector
            )

        out["histo"] = histo
