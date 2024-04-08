# coding: utf8

from qgis.core import QgsApplication


# avoid "Application path not initialized" message
QgsApplication.setPrefixPath('/usr', True)
qgs = QgsApplication([], False)
qgs.initQgis()
