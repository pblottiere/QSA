# QSA REST API : installation

## From sources:

```` shell
$ cd qsa-api
$ virtualenv --system-site-packages venv  # system aware for pyqgis
$ . venv/bin/activate
(venv)$ pip install poetry
(venv)$ poetry install
````

Binary distributions:

## With Docker

QSA-api is already available with `qsa-api` docker image.

Example to run QSA-api:

````shell
$ docker run --rm \
	-p 5000:5000 \
	-e QSA_QGISSERVER_URL=http://xxx.xxx.xxx.xxx/ogc/ \
	-e QSA_QGISSERVER_PROJECTS_DIR=/qsa \
	-e QSA_QGISSERVER_PROJECTS_PSQL_SERVICE=service_name \
	-e PGSERVICEFILE=/home/ubuntu/.pg_service.conf \
	-v folder_with_pgservicefile:/home/ubuntu/ \
	gitlab.hytech-imaging.fr:5050/internal/registry/qsa-api:dev

QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
 * Serving Flask app 'qsa_api.app'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.17.0.2:5000
Press CTRL+C to quit
172.17.0.1 - - [01/Jul/2024 14:36:29] "GET /api/projects/ HTTP/1.1" 200 -
````

Environment variables, mentionned with the `-e` option, are detailled in the `configuration` section. A volume, mentionned with the `-v` option, can be used to provide postgresql service file.