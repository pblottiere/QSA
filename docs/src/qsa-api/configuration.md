# QSA REST API configuration

QSA web server can be configured thanks to the next environment variables:

| Mandatory  | Environment variable            |         Description                               |
|------------|---------------------------------|---------------------------------------------------|
| Yes        | `QSA_QGISSERVER_URL`            | QGIS Server URL                                   |
| Yes        | `QSA_QGISSERVER_PROJECTS`       | Storage location for QGIS projects                |
| No         | `QSA_QGISSERVER_MONITORING_PORT`| Connection port for `qsa-plugin`                  |
| No         | `QSA_MAPPROXY_PROJECTS`         | Storage location for MapProxy configuration files |
