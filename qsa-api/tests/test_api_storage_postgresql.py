import os
import json
import shutil
import unittest
import requests
from flask import Flask
from pathlib import Path

app = Flask(__name__)

from qsa_api.config import QSAConfig
from qsa_api.api.projects import projects
from qsa_api.api.symbology import symbology

from .utils import TestClient

app.register_blueprint(projects, url_prefix="/api/projects")
app.register_blueprint(symbology, url_prefix="/api/symbology")

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

        # data = {}
        # data["name"] = "qsa_test_project1"
        # data["author"] = "pblottiere"
        # p = self.app.post("/api/projects/", data)
        # self.assertEqual(p.status_code, 201)

        # # 2 projects
        # p = self.app.get("/api/projects/")
        # self.assertTrue(TEST_PROJECT_0 in p.get_json())
        # self.assertTrue(TEST_PROJECT_1 in p.get_json())

        # # remove project
        # p = self.app.delete(f"/api/projects/{TEST_PROJECT_0}")
        # self.assertEqual(p.status_code, 201)

        # # 1 projects
        # p = self.app.get("/api/projects/")
        # self.assertTrue(TEST_PROJECT_1 in p.get_json())

        # # get info about project
        # p = self.app.get(f"/api/projects/{TEST_PROJECT_1}")
        # j = p.get_json()
        # self.assertTrue("crs" in j)
        # self.assertTrue("creation_datetime" in j)
        # self.assertEqual(j["author"], "pblottiere")

        # # remove last project
        # p = self.app.delete(f"/api/projects/{TEST_PROJECT_1}")
