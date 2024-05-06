# QSA REST API : endpoints

## PostgreSQL schema

When PostgreSQL support is enabled, a query string parameter `schema` may be
used to specify the schema in which the QGIS project is stored in the database
(`public` is used by default).

```` shell
# call a specific endpoint using projects stored in PostgreSQL schema named `myschema`
$ curl "http://localhost/api/xxx/yyy?schema=myschema"
````

## Project

A QSA project is defined by:

* a QGIS project
* a list of themes
* an internal SQLite database
* a MapProxy configuration file (if enabled)

| Method  |                      URL                      |         Description                                                                                 |
|---------|-----------------------------------------------|-----------------------------------------------------------------------------------------------------|
| GET     | `/api/projects`                               | List projects                                                                                       |
| GET     | `/api/projects/{project}`                     | List project's metadata                                                                             |
| POST    | `/api/projects/`                              | Create a project with `name`, `author` and `schema` (only used when PostgreSQL support is enabled)  |
| DELETE  | `/api/projects/{project}`                     | Remove a project                                                                                    |

Examples:

``` shell
# create a project and store the QGIS project in PostgreSQL within `my_schema`
$ curl "http://localhost/api/projects/" \
     -X POST \
     -H 'Content-Type: application/json' \
     -d '{
        "name":"my_project",
        "author":"pblottiere",
        "schema":"my_schema"
     }'

# get metadata about the project stored in PostgreSQL
$ curl "http://localhost/api/projects/my_project?schema=my_schema"
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
| POST    | `/api/projects/{project}/layers/{layer}/style`   | Add/Update layer's style with `name` (style name) and `current` (`true` or `false`)      |
| DELETE  | `/api/projects/{project}/layers/{layer}`         | Remove layer from project                                                                |

Example:

```` shell
# Add a FlatGeobuf vector layer in project `my_project`
$ curl "http://localhost/api/projects/my_project/layers" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "crs": 4326,
    "name":"my_layer",
    "type":"vector",
    "datasource":"/vsis3/my-storage/vector/my_layer.fgb",
  }'
````

## Symbology

Vector layers rendering can be configured with several kinds of symbols
according to the geometry type. The [symbol selector](https://docs.qgis.org/3.34/en/docs/user_manual/style_library/symbol_selector.html)
in QGIS is very dense but for now, only Marker, Line and Fill simple symbols
are supported. The `/api/symbology` endpoint allows to dynamically retrieve the
corresponding parameters depending on QGIS Server version.

| Method  |                      URL                                      |         Description                          |
|---------|---------------------------------------------------------------|----------------------------------------------|
| GET     | `/api/symbology/vector/point/single_symbol/marker/properties` | Marker simple symbol properties              |
| GET     | `/api/symbology/vector/line/single_symbol/line/properties`    | Line simple symbol properties                |
| GET     | `/api/symbology/vector/polygon/single_symbol/fill/properties` | Polygon simple symbol properties             |
| GET     | `/api/symbology/vector/rendering/properties` | Vector layer rendering properties                             |
| GET     | `/api/symbology/raster/singlebandgray/properties`             | Single band gray properties                  |
| GET     | `/api/symbology/raster/multibandcolor/properties`             | Multi band color properties                  |
| GET     | `/api/symbology/raster/rendering/properties`                  | Raster layer rendering properties            |

Examples:

```` shell
# Return single symbol properties for polygon layers
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

# Return multi band gray properties for raster layers
$ curl "http://localhost:5000/api/symbology/raster/multibandcolor/properties" | jq
{
  "blue": {
    "band": 3
  },
  "green": {
    "band": 2
  },
  "red": {
    "band": 1
  }
  "contrast_enhancement": "StretchToMinimumMaximum (StretchToMinimumMaximum, NoEnhancement, StretchAndClipToMinimumMaximum, ClipToMinimumMaximum)"
}
````


## Style

A QSA style may be used through the `STYLE` OGC web services parameter to
specify the rendering for a specific layer. Default styles may be defined and
automatically used when a vector layer is added to a QSA project.

| Method  |                      URL                      |         Description                                                                                                            |
|---------|-----------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| GET     | `/api/projects/{project}/styles`              | List styles in project                                                                                                         |
| GET     | `/api/projects/{project}/styles/default`      | List default styles in project                                                                                                 |
| GET     | `/api/projects/{project}/styles/{style}`      | List style's metadata                                                                                                          |
| POST    | `/api/projects/{project}/styles/{style}`      | Add style to project. See [Vector style](#vector-style) and [Raster style](#raster-style) for more information.                |
| POST    | `/api/projects/{project}/styles/default`      | Set a default layer's style. See [Vector style](#vector-style) and [Raster style](#raster-style) for more information.         |
| DELETE  | `/api/projects/{project}/styles/{style}`      | Remove style from project                                                                                                      |


#### Vector style {#vector-style}

For vector layers, a style can be defined with the parameters listed below:
- `type` : `vector`
- `name` : the name of the style
- `rendering` : rendering parameters (only `opacity` is supported for now)
- `symbology` : dictionary with `type` (only `single_symbol` is supported for
                now), `symbol` and `properties`

Example:

```` shell
# Add a style for point geometry vector layers
$ curl "http://localhost:5000/api/projects/my_project/styles" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "vector",
    "name": "my_marker_style",
    "rendering": {
      "opacity": 100.
    },
    "symbology": {
      "type": "single_symbol",
      "symbol": "marker",
      "properties": {
        "color": "#112233"
      }
    }
  }'
````

To set a default style for a specific geometry, the parameters listed below are available:
- `name` : the name of the style to use by default
- `geometry` : the geometry for which the style needs to be applied


#### Raster style {#raster-style}

For raster layers, a style can be defined with the parameters listed below:
- `type` : `raster`
- `name` : the name of the style
- `rendering` : rendering parameters
- `symbology` : dictionary with `type` (only `singlebandgray` and
  `multibandcolor` are supported for now) and `properties`

Example:

```` shell
# Add a style for point multiband raster
$ curl "http://localhost:5000/api/projects/my_project/styles" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "raster",
    "name": "my_multiband_style",
    "rendering": {
      "saturation": 3,
      "brightness": -148,
      "contrast": 42,
      "gamma": 4.
    },
    "symbology": {
      "type": "multibandcolor",
      "properties": {
        "red": {
          "band": 1
        },
        "green": {
          "band": 2
        },
        "blue": {
          "band": 3
        }
      }
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
