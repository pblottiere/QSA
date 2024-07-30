# QGIS Server Administration

[![CI](https://img.shields.io/github/actions/workflow/status/pblottiere/QSA/tests.yml)](https://github.com/pblottiere/QSA/actions)
[![Release](https://img.shields.io/badge/release-0.0.2-green.svg)](https://github.com/pblottiere/QSA/releases)
[![Documentation](https://img.shields.io/badge/docs-Book-informational)](https://pblottiere.github.io/QSA/)

Components:

* `qsa-api`: Flask web server with a REST API for administrating QGIS Server
* `qsa-plugin`: QGIS Server plugin for introspection
* `qsa-cli`: Command line tool

Main features:
* Create and manage QGIS projects stored on filesystem or in PostgreSQL
* Create and update vector and raster layers: symbology, theme, ...
* Inspect online QGIS Server instances
* Cache management with MapProxy


See QGIS Server Administration tool's [documentation](https://pblottiere.github.io/QSA/) for more details.
