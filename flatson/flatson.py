# -*- coding: utf-8 -*-
import json


class Flatson(object):
    def __init__(self, schema):
        self.schema = schema
        self.fieldnames = self._build_fieldnames()

    def _build_fieldnames(self):
        return [k for k in self.schema.get('properties', {})]

    @classmethod
    def from_schemafile(cls, schemafile):
        with open(schemafile) as f:
            return cls(json.load(f))

    def flatten(self, obj):
        return [obj.get(p) for p in self.fieldnames]
