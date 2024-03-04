# QSA REST API

[Flask](https://flask.palletsprojects.com/en/3.0.x/) WSGI server providing a
REST API for managing QGIS Server.

Features:

- Create and manage projects stored in PostgreSQL and filesystem
- Add and update vector layers based on multiple datasources (AWS S3 buckets, ...)
- Configure symbology and themes based on simple symbols parameters

Optional features:

- Cache management with MapProxy
- Interaction with online QGIS Server instances (depends on [QSA
  plugin](qsa-plugin/))
