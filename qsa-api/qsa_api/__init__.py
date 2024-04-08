# coding: utf8

import os
from qgis.core import QgsApplication


# avoid "Application path not initialized" message
os.environ["QT_QPA_PLATFORM"] = "offscreen"

QgsApplication.setPrefixPath('/usr', True)
qgs = QgsApplication([], False)
qgs.initQgis()
