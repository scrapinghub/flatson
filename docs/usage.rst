.. _usage:

=============
Using Flatson
=============


Using Flatson is simple, you just need some JSON data to flatten and its `JSON
schema`_. Flatson will use the information from the schema to understand the
structure of your object, which makes the flattening easier and more
predictable.


.. note::
    If you don't have the JSON schema for the data you want to flatten, you can
    use a tool to generate a JSON schema for your data, like `Skinfer`_ or
    http://jsonschema.net.

Walk-through with an example
----------------------------

Say you have the following JSON schema in a file named ``schemafile.json``::

    {
        "$schema": "http://json-schema.org/draft-04/schema",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "number"},
            "address": {
                "type": "object",
                "properties": {"city": {"type": "string"}, "street": {"type": "string"}}
            },
            "skills": {"type": "array", "items": {"type": "string"}}
        }
    }

You can instantiate the :class:`~.Flatson` class for this schemafile like this::

    >>> from flatson import Flatson
    >>> f = Flatson.fromschemafile('schemafile.json')
    >>> f.fieldnames
    ['address.city', 'address.street', 'age', 'name', 'skills']

Note how Flatson has inferred the flattened field names, which you
can access through the :attr:`~.Flatson.fieldnames` property.

Let's test it with some sample data::

    >>> sample = {
                "name": "Claudio", "age": 42,
                "address": {"city": "Paris", "street": "Rue de Sevres"},
                "skills": ["hacking", "soccer"]}
    >>> f.flatten(sample)
    ['Paris', 'Rue de Sevres', 42, 'Claudio', '["hacking","soccer"]']

There are a couple of things to note here:

1) the :meth:`~.Flatson.flatten` method simply returns a list of simple objects
2) the array is by default serialized as a JSON string

.. note::
    Array serialization is :ref:`a topic apart <array-serialization>`, for now
    it suffices to say that if you don't like this default behavior, there are
    other options you can configure through the schema, you can even register
    your own serialization methods if you like.

Say you actually want a Python dict instead of a list, no worries, just use
:meth:`~.Flatson.flatten_dict`::

    >>> f.flatten_dict(sample)
    OrderedDict([('address.city', 'Paris'), ('address.street', 'Rue de Sevres'), ('age', 42), ('name', 'Claudio'), ('skills', '["hacking","soccer"]')])

Note that this returns an OrderedDict instead of a traditional Python dict:
this has the advantage of preserving the same field ordering of the the list
returned by the :meth:`~.Flatson.flatten` method.

.. _array-serialization:

Array serialization
-------------------

TODO: write about array serialization here, point to design decisions, list available methods

.. _JSON schema: http://spacetelescope.github.io/understanding-json-schema/index.html
.. _Skinfer: https://github.com/scrapinghub/skinfer
