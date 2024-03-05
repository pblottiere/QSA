Welcome to QGIS Server Administration tool's documentation.


[QGIS Server](https://docs.qgis.org/3.34/en/docs/server_manual/introduction.html) is
a map server-based on the QGIS core library and rendering engine which provides
numerous classical services like WMS, WFS, WCS, WMTS and OGC API Features. While
QGIS Desktop acts like a WYSIWYG tool for setting up projects, the need for a
REST API is sometime necessary to configure and administrate QGIS Server. The
aim of the QSA project is to provide such an API and tools.


Components:

* [QSA REST API](qsa-api/): Flask web server with a REST API for administrating QGIS Server
* [QSA plugin](qsa-plugin/): QGIS Server plugin for introspection
* [QSA cli](qsa-cli/): Command line tool

Features:
* Cache management with MapProxy
* Create and manage QGIS projects stored on filesystem
* Create and update vector layers : symbology, theme, ...

Roadmap:
* Add more documentation
* Add raster layer support
* Add PostgreSQL support to store QGIS projects
* Publish `qsa-cli` on PyPI
* Publish a `qsa-api` Docker image on DockerHub
* Publish `qsa-plugin` on QGIS plugin repository
