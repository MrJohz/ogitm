import pygit2 as pg2


_SIGNATURE = pg2.Signature('OGitM', '-')


class TreeWrapper:

    def __init__(self, repo):
        self._repo = repo
        self._tree = None

    def __setitem__(self, name, text):
        if self._tree is None:
            self._tree = self._make_tree()

        blob_id = self._repo.create_blob(text)
        self._tree.insert(name, blob_id, pg2.GIT_FILEMODE_BLOB)

    def __getitem__(self, name):
        if self._tree is not None:
            return self._get_from_working_copy(name)
        else:
            return self._get_from_head(name)

    def _get_from_working_copy(self, name):
        entry = self._tree.get(name)
        if entry is None:
            raise KeyError('{name} not in current tree'.format(name=name))
        return self._repo[entry.id].data.decode('utf-8')

    def _get_from_head(self, name):
        entry = self._get_tree()[name]
        return self._repo[entry.id].data.decode('utf-8')

    def __delitem__(self, name):
        if self._tree is None:
            self._tree = self._make_tree()

        self._tree.remove(name)

    def __contains__(self, name):
        if self._tree is None:
            tree = self._get_tree()
            if tree is not None:
                return name in tree
            else:
                return False
        else:
            return self._tree.get(name) is not None

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def clear(self):
        if self._tree is None:
            self._tree = self._make_tree()

        self._tree.clear()

    def save(self, msg=''):
        if self._tree is None:
            return

        tid = self._tree.write()
        self._repo.create_commit(
            'refs/heads/master', _SIGNATURE, _SIGNATURE,
            '', tid, self._get_parents())
        self._tree = None

    def rollback(self):
        self._tree is None

    def _get_parents(self):
        if self._repo.is_empty:
            return []
        else:
            return [self._repo.head.target]

    def _make_tree(self):
        old_tree = self._get_tree()
        if old_tree is None:
            return self._repo.TreeBuilder()
        else:
            return self._repo.TreeBuilder(old_tree)

    def _get_tree(self):
        if self._repo.is_empty:
            return None
        else:
            return self._repo[self._repo.head.target].tree
