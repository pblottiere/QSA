# QSA cli : commands

Command's names are inspired by `Docker`:

```` console
$ qsa --help
Usage: qsa [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  inspect  Returns metadata about a specific QGIS Server instance
  logs     Returns logs of a specific QGIS Server instance
  ps       List QGIS Server instances
  stats    Returns stats of QGIS Server instances
````

Examples:

```` console
$ qsa ps
INSTANCE ID    IP          STATUS
-------------  ----------  -----------------------
336a0fc1       172.20.0.2  Binded 1315 seconds ago
13097056       172.20.0.4  Binded 1315 seconds ago
a523ee7a       172.20.0.5  Binded 1315 seconds ago
d11e11a4       172.20.0.6  Binded 1315 seconds ago
````
