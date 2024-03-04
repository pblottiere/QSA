# Sandbox

The sandbox directory provides a plug-and-play environment to discover QSA
tools.


Up and running:

```` shell
$ docker-compose up --scale qgisserver=4 -d
````


Check QGIS Server instance's:

```` shell
$ export QSA_URL="http://localhost:5000"
$ qsa instances
````
