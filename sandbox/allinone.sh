#! /bin/bash

# create schema and project
psql -h localhost -p 5433 -U qsa qsa -c "create schema my_schema"

curl "http://localhost:5000/api/projects/" \
    -X POST \
    -H 'Content-Type: application/json' \
    -d '{
        "name":"my_project",
        "author":"pblottiere",
        "schema":"my_schema"
    }'

curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "crs": 4326,
    "datasource":"/data.gpkg|layername=polygons",
    "name":"polygons",
    "type":"vector"
  }'

# vector layers
curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "crs": 4326,
    "datasource":"/data.gpkg|layername=lines",
    "name":"lines",
    "type":"vector"
  }'

curl "http://localhost:5000/api/projects/my_project/styles?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "vector",
    "name": "my_fill_style",
    "symbology": {
      "type": "single_symbol",
      "symbol": "fill",
      "properties": {
          "color": "#00BBBB",
          "style": "cross",
          "outline_width": 0.16,
          "outline_color": "#002222"
      }
    },
    "rendering": {}
  }'

curl "http://localhost:5000/api/projects/my_project/layers/polygons/style?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"my_fill_style",
    "current":true
  }'

curl "http://localhost:5000/api/projects/my_project/layers/polygons/map?schema=my_schema" --output map_vector.png

# raster layers
curl "http://localhost:5000/api/projects/my_project/layers?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "crs": 4326,
    "datasource":"/dem.tif",
    "name":"dem",
    "type":"raster"
  }'

curl "http://localhost:5000/api/projects/my_project/styles?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "raster",
    "name": "my_singlebandgray_style",
    "symbology": {
      "type": "singlebandgray",
      "properties": {
        "gray_band": 1,
        "contrast_enhancement": {
          "algorithm": "StretchToMinimumMaximum",
          "limits_min_max": "MinMax"
        }
      }
    },
    "rendering": {"brightnes": 255, "gamma": 0.1, "contrast": 100}
  }'

curl "http://localhost:5000/api/projects/my_project/layers/dem/style?schema=my_schema" \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"my_singlebandgray_style",
    "current":true
  }'

curl "http://localhost:5000/api/projects/my_project/layers/dem/map?schema=my_schema" --output map_raster.png
