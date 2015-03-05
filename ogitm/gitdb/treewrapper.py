import pygit2 as pg2


_SIGNATURE = pg2.Signature('OGitM', '-')


class TreeWrapper:

    def __init__(self, repo):
        self._repo = repo
        self._working_tree = None
        self._last_saved_tree = None
        self._working_contents = {}

    def __setitem__(self, name, text):
        if self._working_tree is None:
            self._new_working_tree()

        blob_id = self._repo.create_blob(text)
        self._working_tree.insert(name, blob_id, pg2.GIT_FILEMODE_BLOB)
        self._working_contents[name] = text

    def __getitem__(self, name):
        if self._working_tree is not None:
            return self._get_from_working_copy(name)
        else:
            return self._get_from_head(name)

    def _get_from_working_copy(self, name):
        entry = self._working_tree.get(name)
        if entry is None:
            raise KeyError('{name} not in current tree'.format(name=name))
        return self._repo[entry.id].data.decode('utf-8')

    def _get_from_head(self, name):
        entry = self._get_tree()[name]
        return self._repo[entry.id].data.decode('utf-8')

    def __delitem__(self, name):
        if self._working_tree is None:
            self._new_working_tree()

        self._working_tree.remove(name)
        if name in self._working_contents:
            del self._working_contents[name]

    def __contains__(self, name):
        if self._working_tree is None:
            tree = self._get_tree()
            if tree is not None:
                return name in tree
            else:
                return False
        else:
            return self._working_tree.get(name) is not None

    def items_list(self):
        if self._working_tree is None:
            return [entry.name for entry in self._get_tree()]
        else:
            l = [entry.name for entry in self._last_saved_tree()]
            l.extend([i for i in self._working_contents])
            return l

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def clear(self):
        if self._working_tree is None:
            self._new_working_tree()

        self._working_tree.clear()
        self._working_contents.clear()

    def save(self, msg=''):
        if self._working_tree is None:
            return

        tid = self._working_tree.write()
        self._repo.create_commit(
            'refs/heads/master', _SIGNATURE, _SIGNATURE,
            '', tid, self._get_parents())
        self._working_tree = None
        self._last_saved_tree = None
        self._working_contents.clear()

    def rollback(self):
        self._working_tree = None
        self._last_saved_tree = None
        self._working_contents.clear()

    def _get_parents(self):
        if self._repo.is_empty:
            return []
        else:
            return [self._repo.head.target]

    def _new_working_tree(self):
        self._last_saved_tree = self._get_tree()
        self._working_contents.clear()
        if self._last_saved_tree is None:
            self._working_tree = self._repo.TreeBuilder()
        else:
            self._working_tree = self._repo.TreeBuilder(self._last_saved_tree)

    def _get_tree(self):
        if self._repo.is_empty:
            return None
        elif self._working_tree is None:
            return self._repo[self._repo.head.target].tree
        else:
            return self._last_tree
