import os
import unittest
from pathlib import Path

from .utils import TestClient

GPKG = Path(__file__).parent / "data.gpkg"
if "QSA_GPKG" in os.environ:
    GPKG = os.environ["QSA_GPKG"]

GEOTIFF = Path(__file__).parent / "landsat_4326.tif"
if "QSA_GEOTIFF" in os.environ:
    GEOTIFF = os.environ["QSA_GEOTIFF"]

TEST_PROJECT_0 = "qsa_test_project0"
TEST_PROJECT_1 = "qsa_test_project1"


class APITestCasePostgresql(unittest.TestCase):
    def setUp(self):
        self.app = TestClient("/tmp/qsa/projects/qgis", "qsa_test")

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
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "qsa_test_project1"
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertEqual(p.status_code, 201)

        # 2 projects
        p = self.app.get("/api/projects/")
        self.assertTrue(TEST_PROJECT_0 in p.get_json())
        self.assertTrue(TEST_PROJECT_1 in p.get_json())

        # remove project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")
        self.assertEqual(p.status_code, 201)

        # 1 projects
        p = self.app.get("/api/projects/")
        self.assertTrue(TEST_PROJECT_1 in p.get_json())

        # get info about project
        p = self.app.get(f"/api/projects/{TEST_PROJECT_1}")
        j = p.get_json()
        self.assertTrue("crs" in j)
        self.assertTrue("creation_datetime" in j)
        self.assertEqual(j["author"], "pblottiere")
        self.assertEqual(j["storage"], "postgresql")
        self.assertEqual(j["schema"], "public")
        self.assertEqual(j["crs"], "EPSG:3857")

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_1}")

    def test_layers(self):
        # add project
        data = {}
        data["name"] = TEST_PROJECT_0
        data["author"] = "pblottiere"
        p = self.app.post("/api/projects/", data)
        self.assertEqual(p.status_code, 201)

        # 0 layer
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers")
        self.assertEqual(p.get_json(), [])

        # add layer
        data = {}
        data["name"] = "layer0"
        data["datasource"] = f"{GPKG}|layername=polygons"
        data["crs"] = 4326
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "layer1"
        data["datasource"] = f"{GPKG}|layername=lines"
        data["crs"] = 4326
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "layer2"
        data["datasource"] = f"{GPKG}|layername=points"
        data["crs"] = 4326
        data["type"] = "vector"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        data = {}
        data["name"] = "layer3"
        data["datasource"] = f"{GEOTIFF}"
        data["crs"] = 4326
        data["type"] = "raster"
        p = self.app.post(f"/api/projects/{TEST_PROJECT_0}/layers", data)
        self.assertEqual(p.status_code, 201)

        # 3 layers
        p = self.app.get(f"/api/projects/{TEST_PROJECT_0}/layers")
        self.assertEqual(
            p.get_json(), ["layer0", "layer1", "layer2", "layer3"]
        )

        # remove last project
        p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")
