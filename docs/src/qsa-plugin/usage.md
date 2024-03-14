# QSA plugin : usage

The QSA plugin starts a TCP socket and tries to connect to the QSA REST API
server every 5 seconds. The next messages are written in QGIS Server logs
during the connection phase:

```` console
Try to connect...
Try to connect...
Try to connect...
Connected with QSA server
````

As soon as the plugin is connected to the QSA Server, you don't need to worry
about anything else.
