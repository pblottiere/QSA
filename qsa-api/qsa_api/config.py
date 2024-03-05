# coding: utf8

import os


class QSAConfig:
    @property
    def is_valid(self) -> bool:
        if self.qgisserver_url and self.qgisserver_projects:
            return True
        return False

    @property
    def monitoring_port(self) -> int:
        return int(os.environ.get("QSA_QGISSERVER_MONITORING_PORT", "0"))

    @property
    def qgisserver_url(self) -> str:
        return os.environ.get("QSA_QGISSERVER_URL", "")

    @property
    def qgisserver_projects(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS", "")

    @property
    def mapproxy_projects(self) -> str:
        return os.environ.get("QSA_MAPPROXY_PROJECTS", "")
