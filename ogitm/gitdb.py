import pygit2 as pg2
import json
from os import path

from .treewrapper import TreeWrapper
from .json_wrapper import JsonDictWrapper


# Used to allow GitDB.transaction() context manager
class _transaction:

    def __init__(self, s):
        self.s = s

    def __enter__(self):
        self.s.begin_transaction()
        self.s._context_managed = True

    def __exit__(self, et, ev, tb):
        self.s._context_managed = False
        if et is not None:
            self.s.rollback()
        else:
            self.s.commit()


class GitDB:

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

    def transaction(self):
        return _transaction(self)

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

    def save(self, msg='-'):
        return self.data_tree.save()

    def get(self, doc_id):
        doc = self.data_tree.get('doc-{id}'.format(id=doc_id))
        if doc is None:
            err = "No such document under id {id}".format(id=doc_id)
            raise ValueError(err)

        return doc

    def find(self, where):
        ids = []

        if len(where) == 0:
            return self.get_all()

        for key, val in where.items():
            index = self.data_tree.get(
                    'index-{key}'.format(key=key), {})

            if isinstance(val, dict):
                ids.append(set(self._find_complex(key, val, index)))
            else:
                ids.append(set(self._find_simple(key, val, index)))

        doc_ids = ids[0]
        for doc_set in ids:
            doc_ids &= doc_set

        docs = []
        for doc_id in doc_ids:
            ds = self.data_tree['doc-{id}'.format(id=doc_id)]
            docs.append(ds)

        return docs

    def _find_simple(self, key, val, index):
        vals = json.dumps(val)
        return index.get(vals, [])

    def _find_complex(self, key, val, index):
        ids = []
        for query, argument in val:
            ids.append()
