#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import

"""
test_flatson
----------------------------------

Tests for `flatson` module.
"""

import json
import os
import skinfer
import unittest

from flatson import Flatson
import tempfile


EMPTY_SCHEMA = skinfer.generate_schema({})

SIMPLE_SCHEMA = skinfer.generate_schema({'a_prop': ''})

LIST_SCHEMA = skinfer.generate_schema([])


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

    def test_no_support_for_list_objects(self):
        with self.assertRaises(ValueError):
            Flatson(schema=LIST_SCHEMA)

    def test_when_no_declared_properties_flatten_empty_list(self):
        f = Flatson(schema=EMPTY_SCHEMA)
        result = f.flatten({'a_prop': 'a_value'})
        self.assertEquals([], result)

    def test_convert_simple_objects(self):
        f = Flatson(schema=SIMPLE_SCHEMA)
        self.assertEquals(['a_prop'], f.fieldnames)
        self.assertEquals(['a_value'], f.flatten({'a_prop': 'a_value'}))
        self.assertEquals([None], f.flatten({}))

    def test_convert_nested_objects(self):
        contain_nested_object = {
            'first': 'hello',
            'second': {
                'one': 1,
                'two': 2,
            }
        }
        schema = skinfer.generate_schema(contain_nested_object)
        f = Flatson(schema=schema)
        self.assertEquals(['first', 'second.one', 'second.two'], f.fieldnames)
        self.assertEquals(['hello', 1, 2], f.flatten(contain_nested_object))

    def test_convert_deep_nested_objects(self):
        contain_nested_object = {
            'first': 'hello',
            'second': {
                'one': {
                    'a': 1,
                    'b': 2,
                },
                'two': {
                    'a': 3,
                    'b': 4,
                },
            }
        }
        schema = skinfer.generate_schema(contain_nested_object)
        f = Flatson(schema=schema)
        self.assertEquals(['first', 'second.one.a', 'second.one.b', 'second.two.a', 'second.two.b'], f.fieldnames)
        self.assertEquals(['hello', 1, 2, 3, 4], f.flatten(contain_nested_object))

if __name__ == '__main__':
    unittest.main()
