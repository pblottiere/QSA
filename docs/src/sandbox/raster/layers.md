# Sandbox : raster layers

Layer is based on the `landsat_4326.tif` file mounted in the Docker containers.


### Add layers

To add a raster layer to a project:

```` shell
$ curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "datasource":"/dem.tif",
    "name":"dem",
    "type":"raster"
  }'
true
````


### List layers and get metadata

```` shell
$ curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema"
["polygons","dem"]
````


### Map sample

To execute a WMS `GetMap` request with basic parameters:

```` shell
$ curl "http://localhost:5000/api/projects/my_project/layers/dem/map?schema=my_schema" --output map.png
````

<img src="../../images/raster_dem_map.png" width="300">
