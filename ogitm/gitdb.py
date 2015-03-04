import pygit2 as pg2
import json


SIGNATURE = pg2.Signature('OGITM', '-')


class TreeWrapper:

    def __init__(self, repo):
        self._repo = repo
        self._tree = self._make_new_tree()

    def __setitem__(self, name, text):
        blob_id = self._repo.create_blob(text)
        self._tree.insert(name, blob_id, pg2.GIT_FILEMODE_BLOB)

    def __getitem__(self, name):
        entry = self._tree.get(name)
        if entry is None:
            raise KeyError('{name} not in current tree'.format(name=name))
        return self._repo[entry.id].data.decode('utf-8')

    def __delitem__(self, name):
        self._tree.remove(name)

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def clear(self):
        self._tree.clear()

    def save(self, msg=''):
        tid = self._tree.write()
        self._repo.create_commit(
            'refs/heads/master', SIGNATURE, SIGNATURE,
            '', tid, self._get_parents())
        self._tree = self._make_new_tree()

    def _get_parents(self):
        if self._repo.is_empty:
            return []
        else:
            return [self._repo.head.target]

    def _make_new_tree(self):
        if self._repo.is_empty:
            return self._repo.TreeBuilder()
        else:
            old_tree = self._repo[self._repo.head.target].tree
            return self._repo.TreeBuilder(old_tree)


class GitDB:

    def _get_next_id(self):
        if hasattr(self, "_id"):
            self._id += 1
        else:
            self._id = 0

        return self._id

    def __init__(self, location):
        self.repo = pg2.init_repository(location, bare=True)
        self.current_tree = TreeWrapper(self.repo)

    def insert(self, document):
        d_id = self._get_next_id()
        self.current_tree['doc-{id}'.format(id=d_id)]
        self.current_tree.save('insert doc-{id}'.format(id=d_id))
        return d_id

    def save(self, msg='-'):
        return self.current_tree.save()

    def get(self, doc_id):
        return None
