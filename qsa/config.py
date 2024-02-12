# coding: utf8

__contact__ = "info@hytech-imaging.fr"
__copyright__ = "Copyright (c) 2023 Hytech Imaging"

import yaml
from pathlib import Path


class Config:
    def __init__(self, path: Path) -> None:
        with open(path, "r") as file:
            self.cfg = yaml.safe_load(file)

    @property
    def qgisserver_url(self) -> str:
        return self.cfg["qgisserver"]["url"]

    @property
    def qgisserver_projects(self) -> Path:
        return Path(self.cfg["qgisserver"]["projects"])

    @property
    def mapproxy_projects(self) -> Path:
        return Path(self.cfg["mapproxy"]["projects"])
