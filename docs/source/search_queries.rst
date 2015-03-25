Searching In GitDB
==================


Similarly to MongoDB, GitDB queries can either be really simple checks of
equality, or more complex tests of a value using Python's extensive set of
methods and functions.  This page will describe how to use the search
functions, for information on writing your own, see
:py:mod:`.gitdb.search_functions`.  There is also an extensive testing suite
for searching in the ``tests/test_gitdb.py`` file.

We will use a model that looks like this:

.. code-block:: python3

    >>> import tempfile; db_directory = tempfile.TemporaryDirectory()
    >>>
    >>> import ogitm
    >>> class MyModel(ogitm.Model, db=db_directory.name):
    ...     name = ogitm.fields.String()
    ...     age = ogitm.fields.Integer()
    ...     has_hair = ogitm.fields.Boolean()
    >>> bob = MyModel(name="Bob", age=93, has_hair=False)
    >>> bert = MyModel(name="Bert", age=23, has_hair=True)
    >>> bex = MyModel(name="Bex", age=32, has_hair=True)
    >>> bub = MyModel(name="Bubba", age=3243, has_hair=False)


Scalar Searches
---------------

Checking if something equals something else is the easiest check of all.

.. code-block:: python3

    >>> MyModel.find(name="Bex").first() == bex
    True
    >>> MyModel.find(age=34).all()
    []
    >>> len(MyModel.find(has_hair=True))
    2


Comparison
----------

The comparison operators (``>``, ``<``, ``>=``, ``<=``, and ``==``) are
supported with aliases.  Generally, the query ``a={'>': b}`` will return all
values of ``a`` such that ``a > b``.

+----------+-----------+--------------------------+
| Operator | Shorthand | Longhand                 |
+==========+===========+==========================+
| ``>``    | ``'gt'``  | ``'greater-than'``       |
+----------+-----------+--------------------------+
| ``<``    | ``'lt'``  | ``'less-than'``          |
+----------+-----------+--------------------------+
| ``>=``   | ``'gte'`` | ``'greater-than-equal'`` |
+----------+-----------+--------------------------+
| ``<=``   | ``'lte'`` | ``'less-than-equal'``    |
+----------+-----------+--------------------------+
| ``==``   | ``'eq'``  | ``'equal'``              |
+----------+-----------+--------------------------+

.. code-block:: python3

    >>> len(MyModel.find(age={'lt': 30}))
    1
    >>> len(MyModel.find(age={'gte': 32}))
    3

    >>> # Note that this also works for any
    >>> # other type with a total ordering
    >>> len(MyModel.find(name={'lt': 'Bf'}))
    2
    >>> # 'eq' will work for any two equivalent items
    >>> MyModel.find(name={'eq': 'Bert'}) == MyModel.find(name='Bert')
    True


String Checks
-------------

String types can be checked using the various :py:meth:`~str.is*` string
methods, as well as :py:meth:`~str.startswith` and :py:meth:`~str.endswith`.
These are hardcoded, but delegate to the string's natural methods.  If you can
think of some way of automatically selecting all string methods that return a
boolean, please let me know!

.. code-block:: python3

    >>> len(MyModel.find(name={'startswith': 'B'}))
    4
    >>> len(MyModel.find(name={'isalpha': True}))
    4


Existence
---------

Testing for existence isn't usually necessary when using models, as (assuming
that you only use the model to insert documents), you know that the only fields
that will exist will be the fields you inserted.  It is more useful when using
arbitrary documents with the raw GitDB instance.  However, the syntax of the
check is the same in both cases.

.. code-block:: python3

    >>> len(MyModel.find(name={'exists': True}))
    4
    >>> len(MyModel.find(name={'exists': False}))
    0
