"""A json-converting `dict` wrapper

This class is designed to be uses in cases where a dict-like interface is to
be used, but all items need to be passed via json-conversion into and out of
the dict.  It wraps around any dict-like object (that is, any object that
implements the dictionary interface).  All methods are delegated to the
wrapped mapping once json-conversion has been performed, so if the wrapped
mapping doesn't have certain methods, this class will raise an error if those
methods are called on it.
"""


import json
from ..compat import MutableMapping


class JsonDictWrapper(MutableMapping):

    def __init__(self, d):
        self._d = d

    def __len__(self):
        return len(self._d)

    def __getitem__(self, item):
        return json.loads(self._d[item])

    def __setitem__(self, item, val):
        self._d[item] = json.dumps(val)

    def __delitem__(self, item):
        del self._d[item]

    def __iter__(self):
        return self._d.__iter__()

    def __getattr__(self, name):
        return getattr(self._d, name)
