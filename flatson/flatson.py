# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
import json


def propgetter(path):
    if '.' in path:
        first_key, rest = path.split('.', 1)
        return lambda x: propgetter(rest)(x.get(first_key, {}))
    else:
        return lambda x: x.get(path, None)


class Flatson(object):
    def __init__(self, schema, field_sep='.', *args, **kwargs):
        self.schema = schema
        self.field_sep = field_sep
        self.fieldnames = self._build_fieldnames_from_schema(schema)
        self.serialize_array = self._get_serialization(kwargs.pop('serialize_with', 'json'))
        self._field_getters = {k: propgetter(k) for k in self.fieldnames}
        self.restval = "\\N"

    @classmethod
    def from_schemafile(cls, schemafile):
        with open(schemafile) as f:
            return cls(json.load(f))

    def flatten(self, obj):
        return [f.getter(obj) for f in self.fieldnames]

    @staticmethod
    def _build_fieldnames_from_schema(schema, field_sep='.'):
        assert schema.get('type') == 'object', "Given schema is not of an object"

        def get_flattened_fields(obj_schema):
            assert schema.get('properties'), "Object should have properties explicited"

            fields = []
            for key, value in obj_schema['properties'].items():
                if value['type'] == 'object':
                    for ff in get_flattened_fields(value):
                        fields.append('{prefix}{fsep}{extension}'.format(prefix=key,fsep=field_sep, extension=ff))
                else:
                    fields.append(key)
            return fields

        fields = get_flattened_fields(schema)
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
        new_data = {k: self._serialize(self._field_getters[k](data)) for k in self.fieldnames}
        data.update(new_data)
        return new_data

    def _serialize(self, datum):
        array_types = (tuple, list)

        if isinstance(datum, array_types):
            return self.serialize_array(datum)

        if isinstance(datum, (bool, int)):
            return str(int(datum))
        return datum

    def flat(self, data):
        self.adapt(data)
        for key, val in data.items():
            if key in self.fieldnames:
                if val is None:
                    val = self.restval
                data[key] = val.encode('utf-8')
        return data


if __name__ == '__main__':
    with open('/home/bbotella/Descargas/schema.json') as f:
        schema = json.loads(f.read())
    flatson = Flatson(schema)

    with open('/home/bbotella/Descargas/properties.jl')as data_file:
        data = [json.loads(line) for line in data_file.readlines()]

    for item in data:
        print(flatson.flat(item))
