OGitM
=====

**Because doing stupid things with git is surprisingly fun.**


.. image:: https://travis-ci.org/MrJohz/ogitm.svg?branch=master
    :target: https://travis-ci.org/MrJohz/ogitm
    :alt: Build Status
.. image:: https://coveralls.io/repos/MrJohz/ogitm/badge.svg?branch=master
    :target: https://coveralls.io/r/MrJohz/ogitm?branch=master
    :alt: Coverage Status
.. image:: https://readthedocs.org/projects/ogitm/badge/?version=latest
    :target: https://readthedocs.org/projects/ogitm/?badge=latest
    :alt: Documentation Status


OGitM is an ORM, but where the relational database that underlies the entire
mapping has been replaced by an awful attempt at replicating a stupidly basic
key-value document store in git_.  This software should never be used by
anyone ever.  Please, for the good of humanity.

.. _git: http://git-scm.com/


Um... What?
-----------

Git is useful, because it stores both data, and the history of that data.
This might be a useful property for a database to have.  Writing a whole
database based on git is boring, I should try writing an ORM to wrap around
it.  Well, it wouldn't so much be an ORM, more an O... git M?


How do I use this?
---------------------

Import the module, declare your model, and go!

.. code-block:: pycon

    >>> import tempfile; db_directory = tempfile.TemporaryDirectory()
    >>>
    >>> import ogitm
    >>> class MyModel(ogitm.Model, db=db_directory.name):
    ...     name = ogitm.fields.String()
    ...     age = ogitm.fields.Integer(min=0)
    >>>
    >>> instance = MyModel(name="Bob", age=172)
    >>> instance_id = instance.save()
    >>> MyModel.find(name="Bob", age=172).first() == instance
    True
    >>> instance.age = -5
    Traceback (most recent call last):
        ...
    ValueError: Disallowed value -5 ...


Can I get at the underlying database?
-------------------------------------

Yes.  Meet the gitdb module, which provides direct access to a document-based
database.  Initialise it with a directory that it can use as a git bare
repository, and start inserting and getting.

.. code-block:: pycon

    >>> import tempfile; db_directory = tempfile.TemporaryDirectory()
    >>>
    >>> from ogitm import gitdb
    >>> db = gitdb.GitDB(db_directory.name)
    >>> doc_id = db.insert({'name': 'Jimmy', 'age': 45, 'car': False})
    >>> db.get(doc_id) == {'name': 'Jimmy', 'age': 45, 'car': False}
    True

More than that, you can also search for documents previously inserted.  These
queries accept simple scalar arguments, which return all documents which have
the same values as the query, and more complex dictionary arguments which can
test for existence, compare etc.

.. code-block:: pycon

    >>> doc_id = db.insert({'name': 'Bobbie', 'car': True})
    >>> doc_id = db.insert({'name': 'Bertie', 'age': 26, 'car': False})
    >>> {'name': 'Bobbie', 'car': True} in db.find_items({'car': True})
    True
    >>> doc_id = db.insert({'name': 'Jimmy'})
    >>> db.find_items({'car': {'exists': False}}) == [{'name': 'Jimmy'}]
    True


Todo
----

- Documentation.  (docstrings & manual)
- PyPI
- Relationships? (U f*cking wot m8?)
- Python 2
- Better way of accessing git (May be needed for Py2, is needed for pypy, will
  make it easier for anyone to install it from PyPI) (See Dulwich)
- Begin versioning sometime fairly soon
