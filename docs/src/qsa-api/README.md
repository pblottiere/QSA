# QSA REST API

`qsa-api` is a [Flask](https://flask.palletsprojects.com/en/3.0.x/) WSGI server
providing a REST API for managing QGIS Server.

Features:

- Create and manage projects stored on filesystem
- Add and update layers based on multiple datasources (AWS S3 buckets, ...)
- Configure symbology and themes based on simple symbols parameters

Optional features:

- Interaction with online QGIS Server instances (depends on [QSA
  plugin](qsa-plugin/))
- Cache management with MapProxy
