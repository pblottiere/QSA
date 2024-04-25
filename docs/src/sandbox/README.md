# Sandbox

The sandbox directory provides a plug-and-play `Docker` environment to discover
QSA tools with PostgreSQL support enabled.


First, a QSA REST API server is set up with 4 QGIS Server instances:

```` shell
$ cd sandbox
$ docker-compose up --scale qgisserver=4 -d
$ docker ps
CONTAINER ID   IMAGE                              COMMAND                  CREATED       STATUS         PORTS                                       NAMES
d2eaf6bdfae4   pblottiere/qsa                     "qsa"                    2 hours ago   Up 9 seconds   0.0.0.0:5000->5000/tcp, :::5000->5000/tcp   sandbox-qsa-1
77fa87641b42   opengisch/qgis-server:3.30-jammy   "/bin/sh -c /usr/loc…"   2 hours ago   Up 9 seconds   80/tcp, 9993/tcp                            sandbox-qgisserver-6
093346c82ea8   opengisch/qgis-server:3.30-jammy   "/bin/sh -c /usr/loc…"   2 hours ago   Up 9 seconds   80/tcp, 9993/tcp                            sandbox-qgisserver-8
afd95ccaef9e   opengisch/qgis-server:3.30-jammy   "/bin/sh -c /usr/loc…"   2 hours ago   Up 9 seconds   80/tcp, 9993/tcp                            sandbox-qgisserver-7
0b13f3d867c5   opengisch/qgis-server:3.30-jammy   "/bin/sh -c /usr/loc…"   2 hours ago   Up 8 seconds   80/tcp, 9993/tcp                            sandbox-qgisserver-1
````
