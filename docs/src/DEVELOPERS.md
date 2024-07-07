# Developers

Documentation:

```` console
$ mdbook build docs
````

Unit tests:

```` console
$ cat ~/.pg_service.conf
[qsa_test]
host=localhost
port=5432
dbname=qsa_test
user=myusername
password=
$ createdb qsa_test
$ cd qsa-api
$ pytest -sv tests
````

Integration tests:

```` console
$ cd sandbox
$ docker-compose up -d
$ cd ../qsa-api
$ QSA_GEOTIFF="/landsat_4326.tif" QSA_GPKG="/data.gpkg" QSA_HOST=127.0.01 QSA_PORT=5000 pytest -sv tests
````
