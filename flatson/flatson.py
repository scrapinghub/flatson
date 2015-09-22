# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
from collections import namedtuple

import json


class Field(namedtuple('Field', 'name getter schema')):
    def is_simple_list(self):
        simple_types = ('number', 'string')
        return self.schema.get('type') == 'array' and self.schema.get('items', {}).get('type') in simple_types


def create_getter(path, field_sep='.'):
    if field_sep in path:
        first_key, rest = path.split(field_sep, 1)
        return lambda x: create_getter(rest)(x.get(first_key, {}))
    else:
        return lambda x: x.get(path, None)


def infer_flattened_field_names(schema, field_sep='.'):
    fields = []

    for key, value in schema.get('properties', {}).items():
        # TODO: add support for configuration through schema
        val_type = value.get('type')
        if val_type == 'object':
            for subfield in infer_flattened_field_names(value):
                full_name = '{prefix}{fsep}{extension}'.format(
                    prefix=key, fsep=field_sep, extension=subfield.name)
                fields.append(Field(full_name, create_getter(full_name), value))
        else:
            fields.append(Field(key, create_getter(key), value))

    return sorted(fields)


class Flatson(object):
    def __init__(self, schema, field_sep='.'):
        self.schema = schema
        self.field_sep = field_sep
        self.fields = self._build_fields()

    @property
    def fieldnames(self):
        return [f.name for f in self.fields]

    def _build_fields(self):
        if self.schema.get('type') != 'object':
            raise ValueError("Schema should be of type object")
        return infer_flattened_field_names(self.schema,
                                           field_sep=self.field_sep)

    @classmethod
    def from_schemafile(cls, schemafile):
        with open(schemafile) as f:
            return cls(json.load(f))

    def _serialize(self, field, obj):
        field_value = field.getter(obj)
        if field.is_simple_list():
            return ','.join([str(x) for x in field_value])
        return field_value

    def flatten(self, obj):
        return [self._serialize(f, obj) for f in self.fields]
