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
    is automatically created under the covers by :py:class:`ogitm.OGitM`, but
    it can also be created and used outside the confines of Object-Model
    mappings.  Total freedom!

    :param str location: The path of the database.
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

        :param str table_name: The name this table will take.
        :raises ValueError: if the name is a reserved table name.
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

        :param str table_name: The name of the table to destroy
        :param bool force: If true, no errors will be raised if the table does
            not exist.

        :raises ValueError: if the table is reserved, or could not be deleted
            for other reasons.
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
        return self._transaction_open

    def begin_transaction(self):
        if self._context_managed:
            m = "Cannot manually manage transaction inside context manager"
            raise ValueError(m)
        elif self._transaction_open:
            m = "Cannot begin transaction when there is an open transaction"
            raise ValueError(m)

        self._transaction_open = True

    def commit(self):
        if self._context_managed:
            m = "Cannot manually manage transaction inside context manager"
            raise ValueError(m)
        elif not self._transaction_open:
            m = "Cannot commit when there is not open transaction"
            raise ValueError(m)

        self._transaction_open = False
        self.save()

    def rollback(self):
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
        if doc_id is None:
            self.data_tree.revert_steps(steps)
        else:
            doc_name = 'doc-{id}'.format(id=doc_id)
            self.data_tree.revert_steps(steps, doc=doc_name)

    def revert_to_state(self, state, doc_id=None):
        self.data_tree.revert_to_state(state)

    def save_state(self):
        return self.data_tree.save_state()

    def insert(self, document):
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
            self.data_tree.save('insert doc-{id}'.format(id=d_id))
        return d_id

    def update(self, d_id, document):
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
            self.data_tree.save('update ' + doc_name)

        return d_id

    def save(self, msg='-'):
        return self.data_tree.save()

    def get(self, doc_id):
        if not isinstance(doc_id, int):
            raise TypeError("id must be an integer")

        doc = self.data_tree.get('doc-{id}'.format(id=doc_id))
        if doc is None:
            err = "No such document under id {id}".format(id=doc_id)
            raise ValueError(err)

        return doc

    def find_ids(self, where):
        return [i[0] for i in self.find(where)]

    def find_items(self, where):
        return [i[1] for i in self.find(where)]

    def find(self, where):
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
