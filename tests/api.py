import json
import shutil
import unittest
from flask import Flask
from pathlib import Path

app = Flask(__name__)

from qsa.config import Config
from qsa.api.projects import projects
from qsa.api.renderers import renderers

app.register_blueprint(projects, url_prefix="/api/projects")
app.register_blueprint(renderers, url_prefix="/api/renderers")

GPKG = Path(__file__).parent.parent / "examples/data/data.gpkg"


class APITestCase(unittest.TestCase):

    def setUp(self):
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

    def test_projects(self):
        # no projects
        p = self.app.get("/api/projects/")
        self.assertEqual(p.get_json(), [])

        # add projects
        data = {}
        data["name"] = "project0"
        data["author"] = "pblottiere"
        p = self.app.post(
            "/api/projects/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertTrue(p.get_json())

        data = {}
        data["name"] = "project1"
        data["author"] = "pblottiere"
        p = self.app.post(
            "/api/projects/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertTrue(p.get_json())

        # 2 projects
        p = self.app.get("/api/projects/")
        self.assertEqual(p.get_json(), ["project0", "project1"])

        # remove project
        p = self.app.delete("/api/projects/project0")
        self.assertTrue(p.get_json())

        # 1 projects
        p = self.app.get("/api/projects/")
        self.assertEqual(p.get_json(), ["project1"])

        # get info about project
        p = self.app.get("/api/projects/project1")
        j = p.get_json()
        self.assertTrue("crs" in j)
        self.assertTrue("creation_datetime" in j)
        self.assertEqual(j["author"], "pblottiere")

    def test_vector_renderers_line(self):
        # list renderers for line geometries
        p = self.app.get("/api/renderers/vector/line")
        self.assertEqual(p.get_json(), ["single_symbol"])

        # access symbol properties
        p = self.app.get("/api/renderers/line/single_symbol/properties")
        j = p.get_json()
        self.assertTrue("line_width" in j)

    def test_vector_renderers_polygon(self):
        # list renderers for line geometries
        p = self.app.get("/api/renderers/vector/polygon")
        self.assertEqual(p.get_json(), ["single_symbol"])

        # list renderers for polygon geometries
        p = self.app.get("/api/renderers/polygon/single_symbol/properties")
        j = p.get_json()
        self.assertTrue("outline_style" in j)

    def test_layers(self):
        # add project
        data = {}
        data["name"] = "project0"
        data["author"] = "pblottiere"
        p = self.app.post(
            "/api/projects/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertTrue(p.get_json())

        # 0 layer
        p = self.app.get("/api/projects/project0/layers")
        self.assertEqual(p.get_json(), [])

        # add layer
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        p = self.app.post(
            "/api/projects/project0/layers",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertTrue(p.get_json())

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        data["crs"] = 32637
        p = self.app.post(
            "/api/projects/project0/layers",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertTrue(p.get_json())

        # 2 layers
        p = self.app.get("/api/projects/project0/layers")
        self.assertEqual(p.get_json(), ["layer0", "layer1"])

        # layer metadata
        p = self.app.get("/api/projects/project0/layers/layer1")
        j = p.get_json()
        self.assertEqual(j["geometry"], "MultiLineString")

        # remove layer0
        p = self.app.delete("/api/projects/project0/layers/layer0")
        self.assertTrue(p.get_json())

        # 1 layer
        p = self.app.get("/api/projects/project0/layers")
        self.assertEqual(p.get_json(), ["layer1"])

    def test_style(self):
        # add project
        data = {}
        data["name"] = "project0"
        data["author"] = "pblottiere"
        p = self.app.post(
            "/api/projects/",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertTrue(p.get_json())

        # 0 style
        p = self.app.get("/api/projects/project0/styles")
        self.assertEqual(p.get_json(), [])

        # add line style to project
        data = {}
        data["name"] = "style_line"
        data["symbology"] = "single_symbol"
        data["geometry"] = "line"
        data["properties"] = {"line_width": 0.5}
        p = self.app.post(
            "/api/projects/project0/styles",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertTrue(p.get_json())

        # add polygon style to project
        data = {}
        data["name"] = "style_polygon"
        data["symbology"] = "single_symbol"
        data["geometry"] = "polygon"
        data["properties"] = {"outline_width": 0.5}
        p = self.app.post(
            "/api/projects/project0/styles",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertTrue(p.get_json())

        # 2 styles
        p = self.app.get("/api/projects/project0/styles")
        self.assertEqual(p.get_json(), ["style_line", "style_polygon"])

        # style line metadata
        p = self.app.get("/api/projects/project0/styles/style_line")
        j = p.get_json()
        self.assertTrue(j["properties"]["line_width"], 0.75)

        # style polygon metadata
        p = self.app.get("/api/projects/project0/styles/style_polygon")
        j = p.get_json()
        self.assertTrue(j["properties"]["outline_width"], 0.75)

        # remove style
        p = self.app.delete('/api/projects/project0/styles/style_polygon')
        self.assertTrue(p.get_json())

        # 1 style
        p = self.app.get("/api/projects/project0/styles")
        self.assertEqual(p.get_json(), ["style_line"])


if __name__ == "__main__":
    unittest.main()
