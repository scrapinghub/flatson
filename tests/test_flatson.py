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

SAMPLE_WITH_LIST_OF_OBJECTS = {
    'first': 'hello',
    'list': [{'key1': 'value1', 'key2': 'value2'}, {'key1': 'value3', 'key2': 'value4'}]
}

SAMPLE_WITH_LIST_OF_TUPLES = {
    'first': 'hello',
    'list': [['value1', 'value2'], ['value3', 'value4']]
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

    def test_flatten_dict(self):
        contain_nested_object = {
            'first': 'hello',
            'second': {
                'one': 1,
                'two': 2,
            }
        }
        schema = skinfer.generate_schema(contain_nested_object)
        f = Flatson(schema=schema)
        expected = {'first': 'hello', 'second.one': 1, 'second.two': 2}
        self.assertEquals(expected, f.flatten_dict(contain_nested_object))

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

    def test_convert_object_with_simple_list_with_default_serialization(self):
        contain_list = {
            'first': 'hello',
            'list': [1, 2, 3, 4],
            'list2': ['one', 'two'],
        }
        schema = skinfer.generate_schema(contain_list)

        f = Flatson(schema=schema)
        self.assertEquals(['first', 'list', 'list2'], f.fieldnames)
        self.assertEquals(['hello', '[1,2,3,4]', '["one","two"]'], f.flatten(contain_list))

    def test_convert_object_with_nested_simple_list_with_default_serialization(self):
        contain_list = {
            'first': 'hello',
            'second': {
                'list1': [1, 2, 3, 4],
                'word': 'world',

            },
        }
        schema = skinfer.generate_schema(contain_list)
        f = Flatson(schema=schema)
        self.assertEquals(['first', 'second.list1', 'second.word'], f.fieldnames)
        self.assertEquals(['hello', '[1,2,3,4]', 'world'], f.flatten(contain_list))

    def test_convert_object_with_simple_list_with_join_serialization(self):
        # given:
        contain_list = {
            'first': 'hello',
            'list': [1, 2, 3, 4],
            'list2': ['one', 'two'],
        }
        schema = skinfer.generate_schema(contain_list)
        serialize_options = dict(method='join_values')
        schema['properties']['list']['flatson_serialize'] = serialize_options

        # when:
        f = Flatson(schema=schema)

        # then:
        self.assertEquals(['first', 'list', 'list2'], f.fieldnames)
        self.assertEquals(['hello', '1,2,3,4', '["one","two"]'], f.flatten(contain_list))

        # and when:
        schema['properties']['list']['flatson_serialize']['separator'] = '+'
        f = Flatson(schema=schema)

        # then:
        self.assertEquals(['hello', '1+2+3+4', '["one","two"]'], f.flatten(contain_list))

    def test_lists_with_objects_with_default_serialization(self):
        # given:
        schema = skinfer.generate_schema(SAMPLE_WITH_LIST_OF_OBJECTS)
        f = Flatson(schema=schema)

        # when:
        result = f.flatten(SAMPLE_WITH_LIST_OF_OBJECTS)

        # then:
        expected = '[{"key1":"value1","key2":"value2"},{"key1":"value3","key2":"value4"}]'
        self.assertEquals(['first', 'list'], f.fieldnames)
        self.assertEquals(['hello', expected], result)

    def test_array_serialization_with_extract_key_values(self):
        # given:
        schema = skinfer.generate_schema(SAMPLE_WITH_LIST_OF_OBJECTS)
        serialize_options = dict(method='extract_key_values')

        # when:
        schema['properties']['list']['flatson_serialize'] = serialize_options
        f = Flatson(schema=schema)
        result = f.flatten(SAMPLE_WITH_LIST_OF_OBJECTS)

        # then:
        expected = 'key1:value1,key2:value2;key1:value3,key2:value4'
        self.assertEquals(['first', 'list'], f.fieldnames)
        self.assertEquals(['hello', expected], result)

    def test_array_serialization_with_extract_key_values_custom_separators(self):
        # given:
        schema = skinfer.generate_schema(SAMPLE_WITH_LIST_OF_OBJECTS)
        serialize_options = dict(method='extract_key_values',
                                 separators=('|', '-', '='))

        # when:
        schema['properties']['list']['flatson_serialize'] = serialize_options
        f = Flatson(schema=schema)
        result = f.flatten(SAMPLE_WITH_LIST_OF_OBJECTS)

        # then:
        expected = 'key1=value1-key2=value2|key1=value3-key2=value4'
        self.assertEquals(['first', 'list'], f.fieldnames)
        self.assertEquals(['hello', expected], result)

    def test_array_serialization_with_extract_first(self):
        # given:
        sample = {'first': 'hello', 'list': ['one', 'two']}
        schema = skinfer.generate_schema(sample)
        serialize_options = dict(method='extract_first')
        schema['properties']['list']['flatson_serialize'] = serialize_options

        # when:
        f = Flatson(schema=schema)
        result = f.flatten(sample)

        # then:
        self.assertEquals(['first', 'list'], f.fieldnames)
        self.assertEquals(['hello', 'one'], result)

        # and when:
        sample2 = {'first': 'hello', 'list': []}
        result = f.flatten(sample2)

        # then:
        self.assertEquals(['first', 'list'], f.fieldnames)
        self.assertEquals(['hello', None], result)

    def test_register_custom_serialization_method(self):
        # given:
        sample = {'first': 'hello', 'list': ['one', 'two']}
        schema = skinfer.generate_schema(sample)
        serialize_options = dict(method='always_one')
        schema['properties']['list']['flatson_serialize'] = serialize_options

        # when:
        f = Flatson(schema=schema)
        f.register_serialization_method('always_one', lambda _v, **kw: '1')
        result = f.flatten(sample)

        # then:
        self.assertEquals(['first', 'list'], f.fieldnames)
        self.assertEquals(['hello', '1'], result)

    def test_disallow_overwriting_official_serialization_methods(self):
        # given:
        sample = {'first': 'hello', 'list': ['one', 'two']}
        schema = skinfer.generate_schema(sample)
        serialize_options = dict(method='always_one')
        schema['properties']['list']['flatson_serialize'] = serialize_options

        # when:
        f = Flatson(schema=schema)
        with self.assertRaises(ValueError):
            f.register_serialization_method('extract_first', lambda _v, **kw: _v[2])


if __name__ == '__main__':
    unittest.main()
