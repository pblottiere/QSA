# coding: utf8

import click
from flask import Flask
from pathlib import Path

from qsa_api.config import QSAConfig
from qsa_api.monitor import QSAMonitor
from qsa_api.api.projects import projects
from qsa_api.api.symbology import symbology
from qsa_api.api.instances import instances


class QSA:
    def __init__(self, cfg: QSAConfig, monitor: QSAMonitor) -> None:
        self.app = Flask(__name__)
        self.app.config["CONFIG"] = cfg
        self.app.config["MONITOR"] = monitor
        self.app.register_blueprint(projects, url_prefix="/api/projects")
        self.app.register_blueprint(symbology, url_prefix="/api/symbology")
        self.app.register_blueprint(instances, url_prefix="/api/instances")

    def run(self):
        self.app.run(host="0.0.0.0")


@click.command()
def run():
    cfg = QSAConfig()
    if not cfg.is_valid:
        return

    monitor = None
    if cfg.monitoring_port:
        monitor = QSAMonitor(cfg)
        monitor.start()

    QSA(cfg, monitor).run()
