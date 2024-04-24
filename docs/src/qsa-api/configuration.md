# QSA REST API : configuration

QSA web server can be configured thanks to the next environment variables:

| Mandatory  | Environment variable                   |         Description                                                          |
|------------|----------------------------------------|------------------------------------------------------------------------------|
| Yes        | `QSA_QGISSERVER_URL`                   | QGIS Server URL                                                              |
| Yes        | `QSA_QGISSERVER_PROJECTS_DIR`          | Storage location on the filesystem for QGIS projects/styles and QSA database |
| No         | `QSA_QGISSERVER_PROJECTS_PSQL_SERVICE` | PostgreSQL service to store QGIS projects and styles                         |
| No         | `QSA_QGISSERVER_MONITORING_PORT`       | Connection port for `qsa-plugin`                                             |
| No         | `QSA_MAPPROXY_PROJECTS_DIR`                | Storage location on the filesystem for MapProxy configuration files          |
