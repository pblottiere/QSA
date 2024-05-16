# coding: utf8

import yaml
import shutil
from pathlib import Path

from .utils import config, qgisserver_base_url


class QSAMapProxy:
    def __init__(self, name: str, schema: str = "") -> None:
        self.name = name
        self.schema = "public"
        if schema:
            self.schema = schema

    def create(self) -> None:
        parent = Path(__file__).resolve().parent
        template = parent / "mapproxy.yaml"
        shutil.copy(template, self._mapproxy_project)

    def remove(self) -> None:
        self._mapproxy_project.unlink()

    def write(self) -> None:
        with open(self._mapproxy_project, "w") as file:
            yaml.safe_dump(self.cfg, file, sort_keys=False)

    def read(self) -> None:
        with open(self._mapproxy_project, "r") as file:
            self.cfg = yaml.safe_load(file)

    def clear_cache(self, layer_name: str) -> None:
        cache_dir = self._mapproxy_project.parent
        for d in cache_dir.glob(f"**/{layer_name}_cache_*"):
            shutil.rmtree(d)

    def add_layer(self, name: str, bbox: list, srs: int, is_raster: bool) -> None:
        if "layers" not in self.cfg:
            self.cfg["layers"] = []
            self.cfg["caches"] = {}
            self.cfg["sources"] = {}

        lyr = {"name": name, "title": name, "sources": [f"{name}_cache"]}
        self.cfg["layers"].append(lyr)

        c = {
            "grids": ["webmercator"],
            "sources": [f"{name}_wms"]
        }
        if is_raster:
            c["use_direct_from_level"] = 14
            c["meta_size"] = [1, 1]
            c["meta_buffer"] = 0
        self.cfg["caches"][f"{name}_cache"] = c

        s = {
            "type": "wms",
            "req": {
                "url": qgisserver_base_url(self.name, self.schema),
                "layers": name,
                "transparent": True,
            },
            "coverage": {"bbox": bbox, "srs": f"EPSG:{srs}"},
        }
        self.cfg["sources"][f"{name}_wms"] = s

    def remove_layer(self, name: str) -> None:
        # early return
        if "layers" not in self.cfg:
            return

        # clean layers
        layers = []
        for layer in self.cfg["layers"]:
            if layer["name"] != name:
                layers.append(layer)
        self.cfg["layers"] = layers

        # clean caches
        cache_name = f"{name}_cache"
        if cache_name in self.cfg["caches"]:
            self.cfg["caches"].pop(cache_name)

        # clean sources
        source_name = f"{name}_wms"
        if source_name in self.cfg["sources"]:
            self.cfg["sources"].pop(source_name)

    @staticmethod
    def _mapproxy_projects_dir() -> Path:
        return Path(config().mapproxy_projects_dir)

    @property
    def _mapproxy_project(self) -> Path:
        return QSAMapProxy._mapproxy_projects_dir() / f"{self.name}.yaml"
