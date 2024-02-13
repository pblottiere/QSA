# QGIS Server Administration

**Disclaimer : WIP!**

QSA is a server providing a REST API for administrating QGIS Server paired with
MapProxy.

### API

Renderers:

- `[GET] /api/symbology/vector/line/single_symbol/line/properties` : list of supported properties
- `[GET] /api/symbology/vector/polygon/single_symbol/fill/properties` : list of supported properties

Projects:

- `[GET] /api/projects/` : list projects
- `[GET] /api/projects/<project_name>` : get project metadata
- `[POST] /api/projects/` : add project
    - `name` : name of the project
    - `author` : author of the project
- `[DELETE] /api/projects/<project_name>` : remove project

Layers:

- `[GET] /api/projects/<project_name>/layers` : list layers in project
- `[GET] /api/projects/<project_name>/layers/<layer_name>` : get layer info (type, CRS, name, ...)
- `[POST] /api/projects/<project_name>/layers` : add layer in project
    - `name` : name of the layer
    - `datasource` : datasource (http url, filesystem path, ...)
    - `crs` : EPSG code
- `[POST] /api/projects/<project_name>/layers/<layer_name>/style` : add style to layer and/or update current style used for rendering
    - `name` : name of the style
    - `current` : `True` to set as default, `False` otherwise
- `[DELETE] /api/projects/<project_name>/layers/<layer_name>` : remove layer

Styles:

- `[GET] /api/projects/<project_name>/styles` : list styles in project
- `[GET] /api/projects/<project_name>/styles/default` : list default styles in project
- `[POST] /api/projects/<project_name>/styles/default` : set default style
    - `symbology` : symbology (only `single_symbol` is supported for now)
    - `geometry` : geometry type (`line` or `polygon`)
    - `symbol` : symbol type (`line` or `fill`)
    - `name` : name of the style
- `[GET] /api/projects/<project_name>/styles/<style_name>` : get style metadata
- `[POST] /api/projects/<project_name>/styles` : add style to project
    - `name` : name of the style
    - `symbology` : symbology (only `single_symbol` is supported for now)
    - `symbol` : only `line` and `fill` are supported for now
    - `properties` : simple symbol properties
- `[DELETE] /api/projects/<project_name>/styles/<style_name>` : remove style


### Configuration

YAML configuration file `qsa.yml`:

``` yaml
qgisserver:
    url: "http://qgisserver/ogc/"
    projects: "/projects/qgis"

mapproxy:
    projects: "/projects/mapproxy"
```


### Run

``` console
$ qsa qsa.yml
```


### Tests

Unit tests:

```` console
$ pytest tests/api.py
````

Integration tests:

```` console
$ QSA_HOST=127.0.0.1 QSA_PORT=5000 QSA_GPKG=/tmp/data.gpkg pytest tests/api.py
````

### Examples

Create an empty project named `project0`:

```` console
$ curl "http://<ip>:<port>/api/projects/" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"name":"project0", "author":"pblottiere"}'
````

List project:

```` console
$ curl "http://<ip>:<port>/api/projects/"
["saint_martin","seine","project0","libye"]
````

Add layer `layer0` based on S3 data in project `project0`:

```` console
$ curl "http://<ip>:<port>/api/projects/project0/layers" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"name":"layer0", "datasource":"/vsis3/hytech-storage-dev/SEINE/Vecteurs/Routes.fgb", "crs": 4326}'
````

List layers in project `project0`:

```` console
$ curl "http://<ip>:<port>/api/projects/project0"
````

Remove project

```` console
$ curl "http://<ip>:<port>/api/projects/project0" -X DELETE
````
