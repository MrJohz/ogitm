import json
import shutil
from os import path
from functools import reduce
from contextlib import contextmanager

import pygit2 as pg2

from .treewrapper import TreeWrapper
from .json_wrapper import JsonDictWrapper
from .search_functions import SearchFunction


__all__ = ['DEFAULT_TABLE', 'RESERVED_TABLE_NAMES', 'GitDB', 'Table']

DEFAULT_TABLE = '__defaulttable__'
RESERVED_TABLE_NAMES = {'__meta__', DEFAULT_TABLE}


class GitDB:
    """The raw database class.

    This class constructs a database instance in the location described.  This
    is automatically created under the covers by :py:class:`ogitm.Model`, but
    it can also be created and used outside the confines of Object-Model
    mappings.  Total freedom!

    Any methods called on GitDB that can't be found will be passed to the
    default :py:class:`~.gitdb.Table` instance, so this class could be used
    as a simple one-table document store without worrying about tables at all.
    This isn't recommended, however.

    Parameters:
        location (str): The path of the database
    """

    def __init__(self, location):
        self.location = location
        self.meta_location = path.join(location, '__meta__')
        self.meta_repo = pg2.init_repository(self.meta_location, bare=True)
        self.meta_tree = JsonDictWrapper(TreeWrapper(self.meta_repo))
        self.default_table = self.table(DEFAULT_TABLE)

    def table(self, table_name):
        """Create a new table.

        This creates a new table in the current database.  You can also use
        the form ``gitdb['table name']``, which delegates to this method.  If
        a table exists, this method will return a new instance of Table
        pointing to the same table.  (Note that two tables pointing to the same
        location will always return equal.)

        Parameters:
            table_name (str): The name this table will take

        Raises:
            ValueError: if the name is a reserved table name
        """
        if table_name in RESERVED_TABLE_NAMES:
            if table_name != DEFAULT_TABLE:
                raise ValueError("Table name " + table_name + " is reserved.")

        tables = self.meta_tree.get('table_list', [])

        if table_name not in tables:
            tables.append(table_name)

        self.meta_tree['table_list'] = tables
        return Table(table_name, path.join(self.location, table_name))

    def __getitem__(self, table_name):
        return self.table(table_name)

    def drop(self, table_name, force=False):
        """Completely and irevocably destroy a table.

        Parameters:
            table_name (str): The name of the table to destroy
            force (bool): If true, no errors will be raised if the table does
                not exist

        Raises:
            ValueError: if the table is reserved, or could not be deleted for
                other reasons
        """
        if table_name in RESERVED_TABLE_NAMES:
            raise ValueError("Table name " + table_name + " is reserved.")

        tables = self.meta_tree.get('table_list', [])
        if table_name not in tables and not force:
            raise ValueError("Table name " + table_name + " does not exist.")
        elif force:
            return

        tables.remove(table_name)
        try:
            shutil.rmtree(path.join(self.location, table_name))
        except OSError as oe:  # pragma: no cover
            msg = "Table name " + table_name + " could not be deleted"
            raise ValueError(msg) from oe

    def __getattr__(self, attr):
        return getattr(self.default_table, attr)


class Table:
    """A class to represent an individual table in a database

    This class should only really  be created by a :py:class:`~.gitdb.GitDB`
    instance, although instantiating it manually won't actually change the way
    this class operates.

    Parameters:
        name (str): The name of the table
        path (str): The path of the table  (Note that this is the path to this
            particular table's location, not the root path of the database.)
    """

    def _get_next_id(self):
        if 'meta-last_id' in self.meta_tree:
            new_meta = int(self.meta_tree['meta-last_id']) + 1
        else:
            self.meta_tree['meta-last_id'] = '0'
            new_meta = 0

        self.meta_tree['meta-last_id'] = str(new_meta)
        self.meta_tree.save()

        return new_meta

    def __init__(self, name, location):
        self.name = name

        self.location = location
        self.dr_loc = path.join(location, 'data')
        self.data_repo = pg2.init_repository(self.dr_loc, bare=True)
        self.data_tree = JsonDictWrapper(TreeWrapper(self.data_repo))

        self.mr_loc = path.join(location, 'meta')
        self.meta_repo = pg2.init_repository(self.mr_loc, bare=True)
        self.meta_tree = TreeWrapper(self.meta_repo)

        self._transaction_open = False
        self._context_managed = False

    def __eq__(self, other):
        return isinstance(other, Table) and other.location == self.location

    @property
    def transaction_open(self):
        """Returns whether there is currently a transaction open.

        Read-only
        """
        return self._transaction_open

    def begin_transaction(self):
        """Opens a new transaction.

        Raises:
            ValueError: if a transaction is already open

        See Also:
            :py:meth:`~.Table.transaction`
                a context manager that automatically handles most of the
                details of a transaction
            :py:meth:`~.Table.commit` and :py:meth:`~.Table.rollback`
                methods for closing the transaction created here
        """
        if self._context_managed:
            m = "Cannot manually manage transaction inside context manager"
            raise ValueError(m)
        elif self._transaction_open:
            m = "Cannot begin transaction when there is an open transaction"
            raise ValueError(m)

        self._transaction_open = True

    def commit(self):
        """Commits all work performed during a transaction.

        Raises:
            ValueError: if this method is called inside the
                :py:meth:`~.Table.transaction` context manager, or if there is
                no open transaction when this method is called

        See Also:
            :py:meth:`~.Table.transaction`
                a context manager that automatically handles most of the
                details of a transaction
            :py:meth:`~.Table.begin_transaction`
                opens up a transaction
            :py:meth:`~.Table.rollback`
                rolls back instead of committing
        """
        if self._context_managed:
            m = "Cannot manually manage transaction inside context manager"
            raise ValueError(m)
        elif not self._transaction_open:
            m = "Cannot commit when there is not open transaction"
            raise ValueError(m)

        self._transaction_open = False
        self.save()

    def rollback(self):
        """Rolls back all work performed during a transaction.

        Raises:
            ValueError: if this method is called inside the
                :py:meth:`~.Table.transaction` context manager, or if there is
                no open transaction when this method is called.

        See Also:
            :py:meth:`~.Table.transaction`
                a context manager that automatically handles most of the
                details of a transaction
            :py:meth:`~.Table.begin_transaction`
                opens up a transaction
            :py:meth:`~.Table.commit`
                commits instead of rolling back
        """
        if self._context_managed:
            m = "Cannot manually manage transaction inside context manager"
            raise ValueError(m)
        elif not self._transaction_open:
            m = "Cannot rollback when there is not open transaction"
            raise ValueError(m)

        self._transaction_open = False
        self.data_tree.rollback()

    @contextmanager
    def transaction(self):
        """A context manager for transactions.

        Sometimes it's more convenient to use with-blocks for transactions.
        This is a context manager to allow that.  When entering the context,
        it calls :py:meth:`~.Table.begin_transaction`.  When leaving the
        context due to normal execution, it will commit all changes.  When
        leaving the context due to an error or exception being raised, it will
        revert all changes, and pass the error on up.

        See Also:
            :py:meth:`~.Table.begin_transaction`, \
                    :py:meth:`~.Table.commit`, \
                    :py:meth:`~.Table.rollback`
                Methods for manually managing a transaction
        """
        self.begin_transaction()
        self._context_managed = True
        try:
            yield
        except:
            self._context_managed = False
            self.rollback()
            raise  # re-raise exception, just checking if exception occurred
        else:
            self._context_managed = False
            self.commit()

    def revert_steps(self, steps, doc_id=None):
        """Reverts the whole database a number of steps.

        Parameters:
            steps (int): The number of steps to revert
            doc_id (int): Not implemented yet

        See Also:
            :py:meth:`~.Table.revert_to_state`
                Another way of reverting changes to the database
        """
        if doc_id is None:
            self.data_tree.revert_steps(steps)
        else:
            doc_name = 'doc-{id}'.format(id=doc_id)
            self.data_tree.revert_steps(steps, doc=doc_name)

    def revert_to_state(self, state, doc_id=None):
        """Reverts the whole database to a previously stored state.

        Parameters:
            state (oid): The state to return to
            doc_id (int): Not implemented yet

        See Also:
            :py:meth:`~.Table.revert_steps`
                Another way of reverting changes to the database
            :py:meth:`~.Table.save_state`
                A method that allows saving the state of the database
        """
        self.data_tree.revert_to_state(state)

    def save_state(self):
        """Returns a marker that can be used later to revert to the same state.

        Because the database is built on top of git, all states are saved, and
        can be checked out.  This method returns a marker to the particular
        commit that refers to the current database.  Note that if the database
        is reverted to a position before this marker, the database can still
        be "for-verted" back to the marker position.

        Returns:
            A save state marker of arbitrary type

        See Also:
            :py:meth:`~.Table.revert_to_state`
                Reverts to states saved by this method
        """
        return self.data_tree.save_state()

    def insert(self, document):
        """Inserts a document into this database.

        Documents are key-value python dicts.  Nested documents are not
        currently tested, and will probably break everything.  Documents also
        can't be scalar objects, although again that is untested and behaviour
        is therefore undefined in that area as well.  Those should probably be
        tested and defined more rigorously.

        Oh, and also the only allowed keys and values are the standard
        primitives (str, int, bool, float, etc), not other objects or
        collections.

        If a transaction is not open, this method will commit all changes into
        the database.

        Parameters:
            document (dict): A key-val single-level dictionary

        Returns:
            int: Document ID
        """
        d_id = self._get_next_id()
        self.data_tree['doc-{id}'.format(id=d_id)] = document

        # set up indexes
        for key, val in document.items():
            val = json.dumps(val)
            index_name = 'index-{key}'.format(key=key)
            index = self.data_tree.get(index_name, {})
            index.setdefault(val, []).append(d_id)
            self.data_tree[index_name] = index

        if not self.transaction_open:
            self.save('insert doc-{id}'.format(id=d_id))
        return d_id

    def update(self, d_id, document):
        """Updates the document at `d_id` with a new document

        This method replaces the document at d_id with a new document,
        completely deleting the old document to replace it with the new
        version.  This is not very efficient.

        See the documentation for :py:meth:`~.Table.insert` for a discussion
        on what actually counts as a document.

        Parameters:
            d_id (int): A previously-saved document id
            document (dict): The document to replace with

        Returns:
            int: Document ID

        Raises:
            ValueError: if the document id does not exist
        """
        doc_name = 'doc-{id}'.format(id=d_id)
        if doc_name not in self.data_tree:
            raise ValueError("Cannot update document that doesn't exist")

        old_doc = self.data_tree[doc_name]
        self.data_tree[doc_name] = document

        # remove old indexes
        for key, val in old_doc.items():
            val = json.dumps(val)
            index_name = 'index-{key}'.format(key=key)
            index = self.data_tree.get(index_name, {})
            index.setdefault(val, []).pop(d_id)
            self.data_tree[index_name] = index

        # insert new indexes
        for key, val in document.items():
            val = json.dumps(val)
            index_name = 'index-{key}'.format(key=key)
            index = self.data_tree.get(index_name, {})
            index.setdefault(val, []).append(d_id)
            self.data_tree[index_name] = index

        if not self._transaction_open:
            self.save('update ' + doc_name)

        return d_id

    def save(self, msg=''):
        """Commits all current unsaved changes

        Normally, this will be automatically called by any methods that
        make changes, or by the transaction methods.  This shouldn't be called
        otherwise, unless in exceptional circumstances (in which case, file an
        issue because something's probably gone wrong.)

        Parameters:
            msg (str): This will become git's commit message
        """
        return self.data_tree.save(msg)

    def get(self, doc_id):
        """Gets a document given it's document id.

        This is the simplest but least useful way of getting information out of
        the database.  It returns the document.

        Parameters:
            doc_id (int): The document ID to fetch

        Returns:
            dict: The document
        """
        if not isinstance(doc_id, int):
            raise TypeError("id must be an integer")

        doc = self.data_tree.get('doc-{id}'.format(id=doc_id))
        if doc is None:
            err = "No such document under id {id}".format(id=doc_id)
            raise ValueError(err)

        return doc

    def find_ids(self, where):
        """Find the ids that match a given query.

        This method is the same as :py:meth:`~.Table.find`, but returns the
        ids rather than (id, doc) pairs.

        Parameters:
            where (dict): Search definition (see :py:meth:`~.Table.find`)

        Returns:
            list[int]: A list of matching document ids
        """
        return [i[0] for i in self.find(where)]

    def find_items(self, where):
        """Find the documents that match a given query.

        This method is the same as :py:meth:`~.Table.find`, but returns the
        documents rather than (id, doc) pairs.

        Parameters:
            where (dict): Search definition (see :py:meth:`~.Table.find`)

        Returns:
            list[dict]: A list of matching documents
        """
        return [i[1] for i in self.find(where)]

    def find(self, where):
        """Finds the documents that match a given query.

        For details on searching, see :doc:`/search_queries`.  Searches in the
        raw :py:class:`~.GitDB` should be documents, rather than keyword
        arguments, but otherwise searches are the same.

        This method returns (id, document) pairs.  There are also the
        convenience methods :py:meth:`~.Table.find_ids` and
        :py:meth:`~.Table.find_items`, which just return the ids and documents
        respectively.

        Parameters:
            where (dict): Search definition

        Returns:
            list[(int, dict)]: A list of matching documents
        """
        all_ids = {int(i[4:]) for i in self.data_tree.items_list()
                   if i.startswith('doc-')}

        id_sets = [all_ids]

        for key, term in where.items():
            index = self.data_tree.get('index-{key}'.format(key=key), {})

            if isinstance(term, dict):
                id_sets.append(self._find_complex(key, term, index, all_ids))

            else:  # simple term, i.e. name="bob"
                id_sets.append(self._find_simple(key, term, index))

        doc_ids = reduce(lambda x, y: x & y, id_sets)

        return [(i, self.data_tree['doc-{id}'.format(id=i)]) for i in doc_ids]

    def find_one(self, where):
        """Finds one document

        This method functions the same as :py:meth:`~.Table.find`, but returns
        just one element, or None if no element found.

        Parameters:
            where (dict): Search definition (see :py:meth:`~.Table.find`)

        Returns:
            *(int, document)* or *None*
        """
        res = self.find(where)
        if len(res) > 0:
            return res[0]
        else:
            return None

    def _find_simple(self, key, val, index):
        vals = json.dumps(val)
        return set(index.get(vals, []))

    def _find_complex(self, key, query, index, al):
        inc_sets = []

        for operator, arg in query.items():
            func = SearchFunction.get(operator)
            inc_sets.append(func(key, operator, arg, index, query, al))

        return reduce(lambda x, y: x & y, inc_sets)
