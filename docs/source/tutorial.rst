The Tutorial
============

Starting with OGitM is usually as simple as writing out the model declaration.

.. code-block:: python3

    >>> import tempfile; db_directory = tempfile.TemporaryDirectory()
    >>> import ogitm

    >>> class Person(ogitm.Model, db=db_directory.name):
    ...
    ...     name = ogitm.fields.String()
    ...     age = ogitm.fields.Integer(min=0)
    ...     hobby = ogitm.fields.Choice(["football", "karate", "knitting"])

Note that the db parameter is mandatory - it specifies the place that the git
repository will be stored.  Currently, this system uses bare repositories.
Additionally, multiple models are stored in the same repository - there aren't
specific tables for each model.  This will change when tables are implemented,
but for now be careful.

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
raising errors all over the place.

.. code-block:: python3

    >>> roberta.age = -3
    Traceback (most recent call last):
        ...
    ValueError: ...

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
    >>> len(Person.find(age={'gt': 2}).find(hobby={'startswith': "k"}))
    2
