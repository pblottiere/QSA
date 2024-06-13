# coding: utf8

import os
from pathlib import Path


class QSAConfig:
    @property
    def is_valid(self) -> bool:
        if self.qgisserver_url and self.qgisserver_projects_dir:
            return True
        return False

    @property
    def gdal_pam_proxy_dir(self) -> Path:
        return Path(os.environ.get("GDAL_PAM_PROXY_DIR", ""))

    @property
    def monitoring_port(self) -> int:
        return int(os.environ.get("QSA_QGISSERVER_MONITORING_PORT", "0"))

    @property
    def qgisserver_url(self) -> str:
        return os.environ.get("QSA_QGISSERVER_URL", "")

    @property
    def qgisserver_projects_dir(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS_DIR", "")

    @property
    def qgisserver_projects_psql_service(self) -> str:
        return os.environ.get("QSA_QGISSERVER_PROJECTS_PSQL_SERVICE", "")

    @property
    def mapproxy_projects_dir(self) -> str:
        return os.environ.get("QSA_MAPPROXY_PROJECTS_DIR", "").replace('"', "")
