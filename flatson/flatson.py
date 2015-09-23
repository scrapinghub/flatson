# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
from collections import namedtuple

import json


class Field(namedtuple('Field', 'name getter schema')):
    def is_array(self):
        return self.schema.get('type') == 'array'

    def is_simple_list(self):
        if not self.is_array():
            return False

        items_type = self.schema.get('items', {}).get('type')
        return items_type in ('number', 'string')

    @property
    def serialization_options(self):
        return self.schema.get('flatson_serialize')


def create_getter(path, field_sep='.'):
    if field_sep in path:
        first_key, rest = path.split(field_sep, 1)
        return lambda x: create_getter(rest)(x.get(first_key, {}))
    else:
        return lambda x: x.get(path, None)


def infer_flattened_field_names(schema, field_sep='.'):
    fields = []

    for key, value in schema.get('properties', {}).items():
        val_type = value.get('type')
        if val_type == 'object':
            for subfield in infer_flattened_field_names(value):
                full_name = '{prefix}{fsep}{extension}'.format(
                    prefix=key, fsep=field_sep, extension=subfield.name)
                fields.append(Field(full_name, create_getter(full_name), subfield.schema))
        else:
            fields.append(Field(key, create_getter(key), value))

    return sorted(fields)


class SerializationMethods(object):
    @staticmethod
    def extract_pairs(array_value, options=None, **kwargs):
        """Serialize array of objects with simple key-values
        """
        options = options or {}
        items_sep = options.get('items_sep', ';')
        pairs_sep = options.get('pairs_sep', ',')
        keys_sep = options.get('keys_sep', ':')
        return items_sep.join(
            pairs_sep.join(keys_sep.join(x) for x in sorted(it.items()))
            for it in array_value)

    @staticmethod
    def extract_first(array_value, options=None, **kwargs):
        return array_value[0]


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

    def _serialize_array_value(self, field, value):
        options = field.serialization_options

        if options:
            if 'method' not in options:
                raise ValueError('Missing method in serialization options for field %s' % field.name)

            try:
                method = getattr(SerializationMethods, options['method'])
            except AttributeError:
                raise ValueError('Unknown serialization method: {method}'.format(**options))
            return method(value, options)

        if field.is_simple_list():
            return ','.join([str(x) for x in value])

        return json.dumps(value)

    def _serialize(self, field, obj):
        value = field.getter(obj)
        if field.is_array():
            return self._serialize_array_value(field, value)
        return value

    def flatten(self, obj):
        return [self._serialize(f, obj) for f in self.fields]
