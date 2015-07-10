#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_flatson
----------------------------------

Tests for `flatson` module.
"""

import json
import os
import unittest

from flatson import Flatson
import tempfile


SIMPLE_SCHEMA = {
    '$schema': u'http://json-schema.org/draft-04/schema',
    'type': 'object',
    'properties': {
        'a_prop': {'type': 'string'},
    },
}


class TestFlatson(unittest.TestCase):
    def test_create(self):
        f = Flatson(schema=SIMPLE_SCHEMA)
        assert f.schema == SIMPLE_SCHEMA

    def test_create_from_schemafile(self):
        _, fname = tempfile.mkstemp()
        try:
            with open(fname, 'w') as f:
                json.dump(SIMPLE_SCHEMA, f)

            obj = Flatson.from_schemafile(fname)
            self.assertEquals(SIMPLE_SCHEMA, obj.schema)
        finally:
            os.remove(fname)

    def test_when_no_declared_properties_flatten_empty_list(self):
        schema = SIMPLE_SCHEMA.copy()
        del schema['properties']
        f = Flatson(schema=schema)
        result = f.flatten({'a_prop': 'a_value'})
        self.assertEquals([], result)

    def test_convert_simple_object(self):
        f = Flatson(schema=SIMPLE_SCHEMA)
        result = f.flatten({'a_prop': 'a_value'})
        self.assertEquals(['a_value'], result)

if __name__ == '__main__':
    unittest.main()
