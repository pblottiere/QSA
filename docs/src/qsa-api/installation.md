# QSA REST API : installation

## From sources

```` shell
$ cd qsa-api
$ virtualenv --system-site-packages venv  # system aware for pyqgis
$ . venv/bin/activate
(venv)$ pip install poetry
(venv)$ poetry install
````

## Docker image

A prebuilt image can be found on `ghcr.io/pblottiere/qsa`. Otherwise the image can be manually be built using: `docker build -t my-custom-qsa-image .` See [Sandbox](sandbox/) for details how to use it.
