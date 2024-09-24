# coding: utf8

from qgis.core import QgsProject


class _Property:
    def __init__(self, scope: str, key: str, entry_type, default):
        self.scope = scope
        self.key = key
        self.type = entry_type
        self.default = default
        self._value = self.default

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, v):
        self._value = self.type(v)

    def update(self, project):
        meth = None
        if self.type == bool:
            meth = project.readBoolEntry
        elif self.type == int:
            meth = project.readNumEntry

        if meth:
            self.value = meth(self.scope, self.key, self.default)[0]


class ProjectProperties:
    def __init__(self) -> None:
        self.props = {}

        # WMS project properties
        wms = {}

        prop = _Property("WMSAddWktGeometry", "/", bool, False)
        wms["getfeatureinfo_geometry"] = prop

        prop = _Property("WMSPrecision", "/", int, 8)
        wms["getfeatureinfo_geometry_precision"] = prop

        self.props["wms"] = wms

    def to_json(self):
        d = {}
        d["wms"] = {}
        for key in self.props["wms"]:
            d["wms"][key] = self.props["wms"][key].value
        return d

    def read(self, project):
        for key in self.props:
            for subkey in self.props[key]:
                self.props[key][subkey].update(project)

    def update(self, data) -> (bool, str):
        for key in data:
            if key not in self.props:
                return False, f"Unsupported key '{key}'"

            for subkey in data[key]:
                if subkey not in self.props[key]:
                    return False, f"Unsupported key '{subkey}'"

                self.props[key][subkey].value = data[key][subkey]

        return True, ""

    def write(self, project) -> (bool, str):
        for key in self.props:
            for subkey in self.props[key]:
                prop = self.props[key][subkey]
                project.writeEntry(prop.scope, prop.key, prop.value)
