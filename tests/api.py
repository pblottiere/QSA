import json
import shutil
import unittest
from flask import Flask
from pathlib import Path

app = Flask(__name__)

from qsa.config import Config
from qsa.api.projects import projects
from qsa.api.symbology import symbology

app.register_blueprint(projects, url_prefix="/api/projects")
app.register_blueprint(symbology, url_prefix="/api/symbology")

GPKG = Path(__file__).parent.parent / "examples/data/data.gpkg"


class APITestCase(unittest.TestCase):

    def _post(self, url, data):
        return self.app.post(
            url,
            data=json.dumps(data),
            content_type="application/json",
        )

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
        p = self._post("/api/projects/", data)
        self.assertTrue(p.get_json())

        data = {}
        data["name"] = "project1"
        data["author"] = "pblottiere"
        p = self._post("/api/projects/", data)
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
        data["name"] = "project0"
        data["author"] = "pblottiere"
        p = self._post("/api/projects/", data)
        self.assertTrue(p.get_json())

        # 0 layer
        p = self.app.get("/api/projects/project0/layers")
        self.assertEqual(p.get_json(), [])

        # add layer
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        p = self._post("/api/projects/project0/layers", data)
        self.assertTrue(p.get_json())

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        data["crs"] = 32637
        p = self._post("/api/projects/project0/layers", data)
        self.assertTrue(p.get_json())

        # 2 layers
        p = self.app.get("/api/projects/project0/layers")
        self.assertEqual(p.get_json(), ["layer0", "layer1"])

        # layer metadata
        p = self.app.get("/api/projects/project0/layers/layer1")
        j = p.get_json()
        self.assertEqual(j["type"], "vector")

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
        p = self._post("/api/projects/", data)
        self.assertTrue(p.get_json())

        # 0 style
        p = self.app.get("/api/projects/project0/styles")
        self.assertEqual(p.get_json(), [])

        # add line style to project
        data = {}
        data["name"] = "style_line"
        data["symbology"] = "single_symbol"
        data["symbol"] = "line"
        data["properties"] = {"line_width": 0.5}
        p = self._post("/api/projects/project0/styles", data)
        self.assertTrue(p.get_json())

        # add fill style to project
        data = {}
        data["name"] = "style_fill"
        data["symbology"] = "single_symbol"
        data["symbol"] = "fill"
        data["properties"] = {"outline_width": 0.5}
        p = self._post("/api/projects/project0/styles", data)
        self.assertTrue(p.get_json())

        # 2 styles
        p = self.app.get("/api/projects/project0/styles")
        self.assertEqual(p.get_json(), ["style_line", "style_fill"])

        # style line metadata
        p = self.app.get("/api/projects/project0/styles/style_line")
        j = p.get_json()
        self.assertTrue(j["properties"]["line_width"], 0.75)

        # style fill metadata
        p = self.app.get("/api/projects/project0/styles/style_fill")
        j = p.get_json()
        self.assertTrue(j["properties"]["outline_width"], 0.75)

        # add layers
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        p = self._post("/api/projects/project0/layers", data)
        self.assertTrue(p.get_json())

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        data["crs"] = 32637
        p = self._post("/api/projects/project0/layers", data)
        self.assertTrue(p.get_json())

        # add style to layers
        data = {}
        data["current"] = False
        data["name"] = "style_fill"
        p = self._post("/api/projects/project0/layers/layer0/style", data)
        self.assertTrue(p.get_json())

        data = {}
        data["current"] = True
        data["name"] = "style_line"
        p = self._post("/api/projects/project0/layers/layer1/style", data)
        self.assertTrue(p.get_json())

        # check style for layers
        p = self.app.get("/api/projects/project0/layers/layer0")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_fill"])
        self.assertEqual(j["current_style"], "default")

        p = self.app.get("/api/projects/project0/layers/layer1")
        j = p.get_json()
        self.assertEqual(j["styles"], ["default", "style_line"])
        self.assertEqual(j["current_style"], "style_line")

        # remove style
        p = self.app.delete("/api/projects/project0/styles/style_fill")
        self.assertTrue(p.get_json())

        # 1 style
        p = self.app.get("/api/projects/project0/styles")
        self.assertEqual(p.get_json(), ["style_line"])

    def test_default_style(self):
        # add project
        data = {}
        data["name"] = "project0"
        data["author"] = "pblottiere"
        p = self._post("/api/projects/", data)
        self.assertTrue(p.get_json())

        # default styles
        p = self.app.get("/api/projects/project0/styles/default")
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
        p = self._post("/api/projects/project0/styles", data)
        self.assertTrue(p.get_json())

        # add fill style to project
        data = {}
        data["name"] = "style_fill"
        data["symbology"] = "single_symbol"
        data["symbol"] = "fill"
        data["properties"] = {"outline_width": 0.5}
        p = self._post("/api/projects/project0/styles", data)
        self.assertTrue(p.get_json())

        # set default styles for polygons/fill symbol
        data = {}
        data["symbology"] = "single_symbol"
        data["geometry"] = "polygon"
        data["symbol"] = "fill"
        data["style"] = "style_fill"
        p = self._post("/api/projects/project0/styles/default", data)
        self.assertTrue(p.get_json())

        # set default styles for line/line symbol
        data = {}
        data["symbology"] = "single_symbol"
        data["geometry"] = "line"
        data["symbol"] = "line"
        data["style"] = "style_line"
        p = self._post("/api/projects/project0/styles/default", data)
        print(p.data)
        self.assertTrue(p.get_json())

        # check default style
        p = self.app.get("/api/projects/project0/styles/default")
        self.assertEqual(
            p.get_json(),
            {
                "line": {"single_symbol": {"line": "style_line"}},
                "polygon": {"single_symbol": {"fill": "style_fill"}},
            },
        )


if __name__ == "__main__":
    unittest.main()
