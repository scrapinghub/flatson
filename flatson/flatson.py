# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
from collections import namedtuple
import json


Field = namedtuple('Field', 'name getter')


class Flatson(object):
    def __init__(self, schema, field_sep='.', *args, **kwargs):
        if not schema.get('type', None) == 'object':
            raise ValueError('schema must be an object')
        self.schema = schema
        self.field_sep = field_sep
        self.fields = self.infer_flattened_field_names(schema)
        self.serialize_array = self._get_serialization(kwargs.pop('serialize_with', 'json'))
        self._field_getters = {k: self._create_getter(k) for k in self.fields}

    @classmethod
    def from_schemafile(cls, schemafile):
        with open(schemafile) as f:
            return cls(json.load(f))

    def _create_getter(self, path, field_sep='.'):
        if field_sep in path:
            first_key, rest = path.split(field_sep, 1)
            return lambda x: self._create_getter(rest)(x.get(first_key, {}))
        else:
            return lambda x: x.get(path, None)

    def infer_flattened_field_names(self, schema, field_sep='.'):
        fields = []

        for key, value in schema.get('properties', {}).items():
            # TODO: add support for configuration through schema
            val_type = value.get('type')
            if val_type == 'object':
                for subfield, _ in self.infer_flattened_field_names(value):
                    full_name = '{prefix}{fsep}{extension}'.format(
                        prefix=key, fsep=field_sep, extension=subfield)
                    fields.append(Field(full_name, self._create_getter(full_name)))
            else:
                fields.append(Field(key, self._create_getter(key)))

        return sorted(fields)

    @staticmethod
    def _get_serialization(strategy):
        if strategy == 'phpserialize':
            import phpserialize
            return lambda it: phpserialize.dumps(it).decode('utf-8')
        elif strategy == 'json':
            return json.dumps
        elif strategy == 'na':
            return lambda x: 'NA' if x else None
        else:
            raise ValueError("Unsupported serialization strategy: %s" % strategy)

    def adapt(self, data):
        new_data = {k: self._serialize(self._field_getters[k](data)) for k in self.fields}
        data.update(new_data)
        return new_data

    def _serialize(self, datum):
        array_types = (tuple, list)

        if isinstance(datum, array_types):
            return self.serialize_array(datum)

        if isinstance(datum, (bool, int)):
            return str(int(datum))
        return datum

    def flatten(self, obj):
        return [f.getter(obj) for f in self.fields]

    @property
    def fieldnames(self):
        return [f.name for f in self.fields]
