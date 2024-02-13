import os
import json
import shutil
import unittest
import requests
from flask import Flask
from pathlib import Path

app = Flask(__name__)

from qsa.config import Config
from qsa.api.projects import projects
from qsa.api.symbology import symbology

app.register_blueprint(projects, url_prefix="/api/projects")
app.register_blueprint(symbology, url_prefix="/api/symbology")

GPKG = Path(__file__).parent.parent / "examples/data/data.gpkg"

TEST_PROJECT_0 = "qsa_test_project0"
TEST_PROJECT_1 = "qsa_test_project1"


class TestResponse:

    def __init__(self, resp, flask_client):
        self.flask_client = flask_client
        self.resp = resp

    def get_json(self):
        if self.flask_client:
            return self.resp.get_json()
        return self.resp.json()


class TestClient:

    def __init__(self):
        self.app = requests
        self._url = ""

        if "QSA_HOST" not in os.environ or "QSA_PORT" not in os.environ:
            self.app = app.test_client()

            # prepare app client
            self.app = app.test_client()

            self.app.application.config["CONFIG"] = Config(
                Path(__file__).parent / "qsa.yml"
            )
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


class APITestCase(unittest.TestCase):

    def setUp(self):
        self.app = TestClient()

    def test_projects(self):
        # no projects
        p = self.app.get("/api/projects/")
        self.assertTrue(TEST_PROJECT_0 not in p.get_json())
        self.assertTrue(TEST_PROJECT_1 not in p.get_json())

        # add projects
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertTrue(p.get_json())

        data = {}
        data["name"] = "qsa_test_project1"
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertTrue(p.get_json())

        # 2 projects
        p = self.app.get("/api/projects/")
        self.assertTrue(TEST_PROJECT_0 in p.get_json())
        self.assertTrue(TEST_PROJECT_1 in p.get_json())

        # remove project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")
        self.assertTrue(p.get_json())

        # 1 projects
        p = self.app.get("/api/projects/")
        self.assertTrue(TEST_PROJECT_1 in p.get_json())

        # get info about project
        p = self.app.get(f"/api/projects/{TEST_PROJECT_1}")
        j = p.get_json()
        self.assertTrue("crs" in j)
        self.assertTrue("creation_datetime" in j)
        self.assertEqual(j["author"], "pblottiere")

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_1}")

    def test_vector_symbology_line(self):
        # access symbol properties
        p = self.app.get(
            "/api/symbology/vector/line/single_symbol/line/properties"
        )
        j = p.get_json()
        self.assertTrue("line_width" in j)

    def test_vector_symbology_fill(self):
        # list symbology for fill geometries
        p = self.app.get(
            "/api/symbology/vector/polygon/single_symbol/fill/properties"
        )
        j = p.get_json()
        self.assertTrue("outline_style" in j)

    def test_layers(self):
        # add project
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertTrue(p.get_json())

        # 0 layer
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers")
        self.assertEqual(p.get_json(), [])

        # add layer
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertTrue(p.get_json())

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        data["crs"] = 32637
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertTrue(p.get_json())

        # 2 layers
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers")
        self.assertEqual(p.get_json(), ["layer0", "layer1"])

        # layer metadata
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer1")
        j = p.get_json()
        self.assertEqual(j["type"], "vector")

        # remove layer0
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}/layers/layer0")
        self.assertTrue(p.get_json())

        # 1 layer
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers")
        self.assertEqual(p.get_json(), ["layer1"])

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")

    def test_style(self):
        # add project
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertTrue(p.get_json())

        # 0 style
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles")
        self.assertEqual(p.get_json(), [])

        # add line style to project
        data = {}
        data["name"] = "style_line"
        data["symbology"] = "single_symbol"
        data["symbol"] = "line"
        data["properties"] = {"line_width": 0.5}
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertTrue(p.get_json())

        # add fill style to project
        data = {}
        data["name"] = "style_fill"
        data["symbology"] = "single_symbol"
        data["symbol"] = "fill"
        data["properties"] = {"outline_width": 0.5}
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertTrue(p.get_json())

        # 2 styles
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles")
        self.assertEqual(p.get_json(), ["style_line", "style_fill"])

        # style line metadata
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles/style_line")
        j = p.get_json()
        self.assertTrue(j["properties"]["line_width"], 0.75)

        # style fill metadata
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles/style_fill")
        j = p.get_json()
        self.assertTrue(j["properties"]["outline_width"], 0.75)

        # add layers
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertTrue(p.get_json())

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        data["crs"] = 32637
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertTrue(p.get_json())

        # add style to layers
        data = {}
        data["current"] = False
        data["name"] = "style_fill"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers/layer0/style", data)
        self.assertTrue(p.get_json())

        data = {}
        data["current"] = True
        data["name"] = "style_line"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers/layer1/style", data)
        self.assertTrue(p.get_json())

        # check style for layers
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer0")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_fill"])
        self.assertEqual(j["current_style"], "default")

        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer1")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_line"])
        self.assertEqual(j["current_style"], "style_line")

        # remove style
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}/styles/style_fill")
        self.assertTrue(p.get_json())

        # 1 style
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles")
        self.assertEqual(p.get_json(), ["style_line"])

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")

    def test_default_style(self):
        # add project
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertTrue(p.get_json())

        # default styles
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles/default")
        self.assertEqual(
            p.get_json(),
            {
                "line": {"single_symbol": {"line": "default"}},
                "polygon": {"single_symbol": {"fill": "default"}},
            },
        )

        # add line style to project
        data = {}
        data["name"] = "style_line"
        data["symbology"] = "single_symbol"
        data["symbol"] = "line"
        data["properties"] = {"line_width": 0.5}
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertTrue(p.get_json())

        # add fill style to project
        data = {}
        data["name"] = "style_fill"
        data["symbology"] = "single_symbol"
        data["symbol"] = "fill"
        data["properties"] = {"outline_width": 0.5}
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles", data)
        self.assertTrue(p.get_json())

        # set default styles for polygons/fill symbol
        data = {}
        data["symbology"] = "single_symbol"
        data["geometry"] = "polygon"
        data["symbol"] = "fill"
        data["style"] = "style_fill"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles/default", data)
        self.assertTrue(p.get_json())

        # set default styles for line/line symbol
        data = {}
        data["symbology"] = "single_symbol"
        data["geometry"] = "line"
        data["symbol"] = "line"
        data["style"] = "style_line"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/styles/default", data)
        self.assertTrue(p.get_json())

        # check default style
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/styles/default")
        self.assertEqual(
            p.get_json(),
            {
                "line": {"single_symbol": {"line": "style_line"}},
                "polygon": {"single_symbol": {"fill": "style_fill"}},
            },
        )

        # add layer
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertTrue(p.get_json())

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        data["crs"] = 32637
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertTrue(p.get_json())

        # check if default style is applied when adding a new layer in the project
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer0")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_fill"])
        self.assertEqual(j["current_style"], "style_fill")

        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers/layer1")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_line"])
        self.assertEqual(j["current_style"], "style_line")

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")


if __name__ == "__main__":
    unittest.main()
