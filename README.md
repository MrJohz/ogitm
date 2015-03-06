# OGitM

![Travis](https://img.shields.io/travis/MrJohz/ogitm.svg?style=flat-square)
![Coveralls](https://img.shields.io/coveralls/MrJohz/ogitm.svg?style=flat-square)


**Because doing stupid things with git is surprisingly fun.**

OGitM is an ORM, but where the relational database that underlies the entire
mapping has been replaced by an awful attempt at replicating a stupidly basic
key-value document store in [git][].  This software should never be used by
anyone ever.  Please, for the good of humanity.

[git]: <http://git-scm.com/>

## Um... What?

Git is useful, because it stores both data, and the history of that data.
This might be a useful property for a database to have.  Writing a whole
database based on git is boring, I should try writing an ORM to wrap around
it.  Well, it wouldn't so much be an ORM, more an O... git M?

## How do I use this?

Currently the only part that's working is the gitdb module, which provides
direct access to a document-based database.  Initialise it with a directory
that it can use as a git bare repository, and start inserting and getting.

    >>> import tempfile; db_directory = tempfile.TemporaryDirectory().name
    >>> from ogitm import gitdb
    >>> db = gitdb.GitDB(db_directory)
    >>> doc_id = db.insert({'name': 'Jimmy', 'age': 45, 'car': False})
    >>> db.get(doc_id) == {'name': 'Jimmy', 'age': 45, 'car': False}
    True

More than that, you can also search for documents previously inserted.  These
queries accept simple scalar arguments, which return all documents which have
the same values as the query, and more complex dictionary arguments which can
test for existence, compare etc.

    >>> doc_id = db.insert({'name': 'Bobbie', 'car': True})
    >>> doc_id = db.insert({'name': 'Bertie', 'age': 26, 'car': False})
    >>> {'name': 'Jimmy', 'age': 45, 'car': False} in db.find({'car': False})
    True
    >>> _ = db.insert({'name': 'Jimmy'})
    >>> db.find({'car': {'exists': False}}) == [{'name': 'Jimmy'}]
    True
