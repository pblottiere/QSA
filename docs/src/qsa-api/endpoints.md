# QSA REST API : endpoints

## Project

A QSA project is defined by:

* a QGIS project
* a list of themes
* a MapProxy configuration file (if enabled)

| Method  |                      URL                      |         Description                        |
|---------|-----------------------------------------------|--------------------------------------------|
| GET     | `/api/projects`                               | List projects                              |
| GET     | `/api/projects/{project}`                     | List project's metadata                    |
| POST    | `/api/projects/`                              | Create a project with `name` and `author`  |
| DELETE  | `/api/projects/{project}`                     | Remove a project                           |

Examples:

``` shell
$ curl "http://localhost/api/projects/" \
     -X POST \
     -H 'Content-Type: application/json' \
     -d '{
        "name":"my_project",
        "author":"pblottiere"
     }'
```

## Layer

When a layer is added/removed to a QSA project, the corresponding QGIS project
is updated. When MapProxy cache management is enabled, the configuration file is
updated as well and the cache may be cleaned if necessary (for example when the
current style is updated).

Several themes can be associated with a layer like in QGIS Desktop, but only
the current one is used when the `STYLE` parameter in OGC web services is
empty.

| Method  |                      URL                         |         Description                                                                      |
|---------|--------------------------------------------------|------------------------------------------------------------------------------------------|
| GET     | `/api/projects/{project}/layers`                 | List layers in project                                                                   |
| GET     | `/api/projects/{project}/layers/{layer}`         | List layer's metadata                                                                    |
| GET     | `/api/projects/{project}/layers/{layer}/map`     | WMS `GetMap` result with default parameters                                              |
| GET     | `/api/projects/{project}/layers/{layer}/map/url` | WMS `GetMap` URL with default parameters                                                 |
| POST    | `/api/projects/{project}/layers`                 | Add layer to project with `type` (`vector` or `raster`), `name`, `datasource` and `crs`  |
| POST    | `/api/projects/{project}/layers/{layer}/style`   | Add/Update layer's style with `name` (style name) and `current` (`True` or `False`)      |
| DELETE  | `/api/projects/{project}/layers/{layer}`         | Remove layer from project                                                                |

Examples:

```` shell
$ curl "http://localhost/api/projects/my_project/layers" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "crs": 4326,
    "name":"my_layer",
    "datasource":"/vsis3/my-storage/vector/my_layer.fgb",
  }'
````

## Symbology

Vector layers rendering can be configured with several kinds of symbols
according to the geometry type. The [symbol selector](https://docs.qgis.org/3.34/en/docs/user_manual/style_library/symbol_selector.html)
in QGIS is very dense but for now, only Marker, Line and Fill simple symbols
are supported. The `/api/symbology` endpoint allows to dynamically retrieve the
corresponding parameters depending on QGIS Server version.

| Method  |                      URL                                      |         Description              |
|---------|---------------------------------------------------------------|----------------------------------|
| GET     | `/api/symbology/vector/point/single_symbol/marker/properties` | Marker simple symbol properties  |
| GET     | `/api/symbology/vector/line/single_symbol/line/properties`    | Line simple symbol properties    |
| GET     | `/api/symbology/vector/polygon/single_symbol/fill/properties` | Polygon simple symbol properties |

Examples:

```` shell
$ curl "http://localhost:5000/api/symbology/vector/polygon/single_symbol/fill/properties" | jq
{
  "border_width_map_unit_scale": "3x:0,0,0,0,0,0",
  "color": "0,0,255,255",
  "joinstyle": "bevel",
  "offset": "0,0",
  "offset_map_unit_scale": "3x:0,0,0,0,0,0",
  "offset_unit": "MM",
  "outline_color": "35,35,35,255",
  "outline_style": "solid (no, solid, dash, dot, dash dot, dash dot dot)",
  "outline_width": "0.26",
  "outline_width_unit": "MM",
  "style": "solid"
}
````


## Style

A QSA style may be used through the `STYLE` OGC web services parameter to
specify the rendering for a specific layer. Default styles may be defined and
used when a layer is added to a project.

| Method  |                      URL                      |         Description                                                                                                            |
|---------|-----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| GET     | `/api/projects/{project}/styles`              | List styles in project                                                                                                         |
| GET     | `/api/projects/{project}/styles/default`      | List default styles in project                                                                                                 |
| GET     | `/api/projects/{project}/styles/{style}`      | List style's metadata                                                                                                          |
| POST    | `/api/projects/{project}/styles/{style}`      | Add style to project with `symbology` (only `single_symbol` is supported for now), `symbol`, `name` and symbology `properties` |
| POST    | `/api/projects/{project}/styles/default`      | Set default style for a specific geometry with `geometry` and `name`                                                           |
| DELETE  | `/api/projects/{project}/styles/{style}`      | Remove style from project                                                                                                      |

Examples:

```` shell
$ curl "http://localhost:5000/api/projects/my_project/styles" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "symbol": "marker",
    "symbology": "single_symbol",
    "name": "my_marker_style",
    "properties": {
      "color": "#112233"
    }
  }'
````


## Instances

When `qsa-plugin` is installed, an `/api/instances` endpoint is available to
retrieve information about QGIS Server underlying instances.

| Method  |                      URL                      |         Description                        |
|---------|-----------------------------------------------|--------------------------------------------|
| GET     | `/api/instances`                              | List online QGIS Server instances          |
| GET     | `/api/instances/{instance}`                   | List QGIS Server instance metadata         |
| GET     | `/api/instances/{instance}/logs`              | Return logs of QGIS Server instance        |
