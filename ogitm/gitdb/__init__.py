import pygit2 as pg2
import json
import shutil
from os import path
from functools import reduce
from contextlib import contextmanager

from .treewrapper import TreeWrapper
from .json_wrapper import JsonDictWrapper
from .search_functions import SearchFunction

RESERVED_TABLE_NAMES = {'__meta__', '__defaulttable__'}


class GitDB:

    def __init__(self, location):
        self.location = location
        self.meta_location = path.join(location, '__meta__')
        self.meta_repo = pg2.init_repository(self.meta_location, bare=True)
        self.meta_tree = JsonDictWrapper(TreeWrapper(self.meta_repo))
        self.default_table = self.table('__defaulttable__')

    def table(self, table_name):
        if table_name in RESERVED_TABLE_NAMES:
            if table_name != '__defaulttable__':
                raise ValueError("Table name " + table_name + " is reserved.")

        tables = self.meta_tree.get('table_list', [])

        if table_name not in tables:
            tables.append(table_name)

        self.meta_tree['table_list'] = tables
        return Table(path.join(self.location, table_name))

    def __getitem__(self, table_name):
        return self.table(table_name)

    def drop(self, table_name, force=False):
        if table_name in RESERVED_TABLE_NAMES:
            raise ValueError("Table name " + table_name + " is reserved.")

        tables = self.meta_tree.get('table_list', [])
        if table_name not in tables and not force:
            raise ValueError("Table name " + table_name + " does not exist.")

        tables.remove(table_name)
        try:
            shutil.rmtree(table_name)
        except OSError:
            msg = "Table name " + table_name + " could not be deleted"
            raise ValueError(msg)

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

    def __init__(self, location):
        self.dr_loc = path.join(location, 'data')
        self.data_repo = pg2.init_repository(self.dr_loc, bare=True)
        self.data_tree = JsonDictWrapper(TreeWrapper(self.data_repo))

        self.mr_loc = path.join(location, 'meta')
        self.meta_repo = pg2.init_repository(self.mr_loc, bare=True)
        self.meta_tree = TreeWrapper(self.meta_repo)

        self._transaction_open = False
        self._context_managed = False

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

        return reduce(lambda x, y: x | y, inc_sets)
