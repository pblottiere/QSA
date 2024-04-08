# Developers

Documentation:

```` console
$ mdbook build docs
````

Unit tests:

```` console
$ cd qsa-api
$ pytest -sv test/api.py
````

Integration tests:

```` console
$ cd sandbox
$ docker-compose up -d
$ cd ../qsa-api
$ QSA_GPKG="/data.gpkg" QSA_HOST=127.0.01 QSA_PORT=5000 pytest -sv tests/api.py
````
