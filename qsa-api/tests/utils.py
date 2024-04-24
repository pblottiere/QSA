import os
import json
import shutil
import requests
from flask import Flask
from pathlib import Path

app = Flask(__name__)

from qsa_api.config import QSAConfig
from qsa_api.api.projects import projects
from qsa_api.api.symbology import symbology

app.register_blueprint(projects, url_prefix="/api/projects")
app.register_blueprint(symbology, url_prefix="/api/symbology")


class TestResponse:
    def __init__(self, resp, flask_client):
        self.flask_client = flask_client
        self.resp = resp

    @property
    def status_code(self):
        return self.resp.status_code

    def get_json(self):
        if self.flask_client:
            return self.resp.get_json()
        return self.resp.json()


class TestClient:
    def __init__(self, projects_dir, projects_psql_service=""):
        self.app = requests
        self._url = ""

        if "QSA_HOST" not in os.environ or "QSA_PORT" not in os.environ:
            self.app = app.test_client()

            # prepare app client
            self.app = app.test_client()

            os.environ["QSA_QGISSERVER_URL"] = "http://qgisserver/ogc/"
            os.environ["QSA_QGISSERVER_PROJECTS_DIR"] = projects_dir
            if projects_psql_service:
                os.environ[
                    "QSA_QGISSERVER_PROJECTS_PSQL_SERVICE"
                ] = projects_psql_service
            self.app.application.config["CONFIG"] = QSAConfig()
            self.app.application.config["DEBUG"] = True

            # clear projects dir
            tmpdir = Path("/tmp/qsa/projects")
            shutil.rmtree(tmpdir, ignore_errors=True)

            (tmpdir / "qgis").mkdir(parents=True, exist_ok=True)
            (tmpdir / "mapproxy").mkdir(parents=True, exist_ok=True)
        else:
            host = os.environ["QSA_HOST"]
            port = os.environ["QSA_PORT"]
            self._url = f"http://{host}:{port}"

            self.delete(f"/api/projects/{TEST_PROJECT_0}")
            self.delete(f"/api/projects/{TEST_PROJECT_1}")

    def post(self, url, data):
        if self.is_flask_client:
            r = self.app.post(
                self.url(url),
                data=json.dumps(data),
                content_type="application/json",
            )
        else:
            r = self.app.post(
                self.url(url),
                data=json.dumps(data),
                headers={"Content-type": "application/json"},
            )
        return TestResponse(r, self.is_flask_client)

    def delete(self, url):
        r = self.app.delete(self.url(url))
        return TestResponse(r, self.is_flask_client)

    def get(self, url):
        r = self.app.get(self.url(url))
        return TestResponse(r, self.is_flask_client)

    def url(self, url) -> str:
        return f"{self._url}{url}"

    @property
    def is_flask_client(self) -> bool:
        return not bool(self._url)
