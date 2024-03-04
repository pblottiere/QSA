# QSA REST API Endpoints

## Symbology

#### Description

TODO

#### Endpoints

| Method  |                      URL                                      |         Description              |
|---------|---------------------------------------------------------------|----------------------------------|
| GET     | `/api/symbology/vector/point/single_symbol/marker/properties` | Marker single symbol properties  |
| GET     | `/api/symbology/vector/line/single_symbol/line/properties`    | Line single symbol properties    |
| GET     | `/api/symbology/vector/polygon/single_symbol/fill/properties` | Polygon single symbol properties |

#### Examples

TODO


## Projects

#### Description

TODO

#### Endpoints

| Method  |                      URL                      |         Description                        |
|---------|-----------------------------------------------|--------------------------------------------|
| GET     | `/api/projects`                               | List projects                              |
| GET     | `/api/projects/{name}`                        | List project's metadata                    |
| POST    | `/api/projects/`                              | Create project with `name` and `author`    |
| DELETE  | `/api/projects/{name}`                        | TODO                                       |

#### Examples

Create a project:

``` json
curl "http://localhost/api/projects/" \
     -X POST \
     -H 'Content-Type: application/json' \
     -d '{
        "name":"project0",
        "author":"pblottiere"
     }'
```


## Layers

#### Description

TODO

#### Endpoints

| Method  |                      URL                      |         Description                                                                 |
|---------|-----------------------------------------------|-------------------------------------------------------------------------------------|
| GET     | `/api/projects/{name}/layers`                 | List layers in project                                                              |
| GET     | `/api/projects/{name}/layers/{name}`          | List layer's metadata                                                               |
| GET     | `/api/projects/{name}/layers/{name}/map`      | WMS `GetMap` result with default parameters                                         |
| GET     | `/api/projects/{name}/layers/{name}/map/url`  | WMS `GetMap` URL with default parameters                                            |
| POST    | `/api/projects/{name}/layers`                 | Add layer to project with `name`, `datasource` and `crs`                            |
| POST    | `/api/projects/{name}/layers/{name}/style`    | Add/Update layer's style with `name` (style name) and `default` (`True` or `False`) |
| DELETE  | `/api/projects/{name}/layers/{name}`          | Remove layer from project                                                           |

#### Examples

Add a vector layer based on AWS S3 bucket:

```` json
curl "http://localhost/api/projects/my_project/layers" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"my_layer",
    "datasource":"/vsis3/my-storage/vector/my_layer.fgb",
    "crs": 4326
  }'
````


## Styles

#### Description

TODO

#### Endpoints

| Method  |                      URL                      |         Description                                                                 |
|---------|-----------------------------------------------|-------------------------------------------------------------------------------------|
| GET     | `/api/projects/{name}/styles`                 | List styles in project                                                              |
| GET     | `/api/projects/{name}/styles/default`         | List default styles in project                                                      |
| GET     | `/api/projects/{name}/styles/{name}`          | List style's metadata                                                               |

#### Examples
