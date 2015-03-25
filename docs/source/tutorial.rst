The Tutorial
============

Using The OGitM Model
---------------------

Starting with OGitM is usually as simple as writing out the model declaration.

.. code-block:: python3

    >>> import tempfile; db_directory = tempfile.TemporaryDirectory()
    >>> import ogitm

    >>> class Person(ogitm.Model, db=db_directory.name):
    ...
    ...     name = ogitm.fields.String()
    ...     age = ogitm.fields.Integer(min=0)
    ...     hobby = ogitm.fields.Choice(["football", "karate", "knitting"],
    ...                                 default="karate")

Note that the db parameter is mandatory - it specifies the place that the git
repository will be stored.  Currently, this system uses bare repositories.
Multiple models stored in the same database location will be stored in
individual tables by default.  (The current implementation uses the
inflection_ library's ``tableize`` method (based on RoR's tableize method).)

.. _inflection: http://inflection.readthedocs.org/en/latest/index.html#inflection.titleize

Here, we've used a string as the path to the directory.  However, we can also
separately instantiate a :py:class:`ogitm.gitdb.GitDB` instance, and use that
instead.  Note that opening two databases with the same directory means that
the two databases will point to the same place.

.. code-block:: python3

    >>> db = ogitm.gitdb.GitDB(db_directory.name)
    >>>
    >>> class AlternatePerson(ogitm.Model, db=db):
    ...     pass

The next thing to do is to start inserting documents into the database.  That's
exactly as simple as it should be.

.. code-block:: python3

    >>> bob = Person(name="bob", age=32, hobby="football")
    >>> geoff = Person(name="geoff", age=18, hobby="knitting")
    >>> roberta = Person(name="roberta", age=42, hobby="football")
    >>> print(bob.age)
    32
    >>> print(geoff.hobby)
    knitting
    >>> print(roberta.name)
    roberta

    >>> bob.age = 33  # Ah, how time changes us all
    >>> bob.hobby = "knitting"
    >>> bob.save() == bob.id
    True

The limitations on the fields will also stop you doing anything stupid by
raising errors all over the place.  They'll also automatically insert default
values.

.. code-block:: python3

    >>> roberta.age = -3
    Traceback (most recent call last):
        ...
    ValueError: ...

    >>> roberta.hobby = "this is not a recognised hobby"
    >>> # Note lack of error message here
    >>> print(roberta.hobby)  # defaults to "karate" as specified in model
    karate

More useful than just storing data is being able to retrieve it later.  The
easiest way to do that is by searching for it.

.. code-block:: python3

    >>> Person.find(name="bob").first() == bob
    True
    >>> Person.find(age=19).all()  # No people aged 19
    []
    >>> Person.find(hobby="knitting").all() == [bob, geoff]
    True

Note that this also works for more complex queries.  We can also chain queries
together.

.. code-block:: python3

    >>> len(Person.find(age={'gt': 2}))  # Matches all current documents
    3
    >>> len(Person.find(age={'gt': 2}, hobby={'startswith': 'kn'}))
    2
    >>> # same as
    >>> len(Person.find(age={'gt': 2}).find(hobby={'startswith': 'kn'}))
    2
    >>> # complex queries may contain more than one operator at a time
    >>> len(Person.find(age={'gt': 2, 'lt': 40}))
    2


Using GitDB Directly
--------------------

Note that OGitM is essentially a wrapper around GitDB.  If you need access to
GitDB as a simple document store, this is possible using the
:py:mod:`ogitm.gitdb` module.

.. code-block:: python3

    >>> import tempfile; db_directory = tempfile.TemporaryDirectory()
    >>> from ogitm import gitdb
    >>> db = gitdb.GitDB(db_directory.name)

A GitDB database is split up into tables.  GitDB automatically creates the
``__defaulttable__`` table, and passes any methods called on it straight to
an internal copy of that table.  This allows for very simple usage of GitDB.
However, it is more likely that a user would want to split up their data into
multiple tables.

.. code-block:: python3

    >>> db.default_table.name
    '__defaulttable__'
    >>> db.table('Table Name')
    <ogitm.gitdb.Table object at ...>
    >>> table = db.table('Table Name')
    >>> doc = table.insert({'my doc': 'your doc'})
    >>> table.get(doc)
    {'my doc': 'your doc'}
    >>> table.find_items({'my doc': 'your doc'})  # Using simple query
    [{'my doc': 'your doc'}]
    >>> table.find_items({'my doc': {'exists': True}})  # Using advanced query
    [{'my doc': 'your doc'}]
