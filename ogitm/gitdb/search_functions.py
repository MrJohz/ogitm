class SearchFunction:

    funcs = {}

    @classmethod
    def add(cls, funcname):
        def _add(func):
            cls.funcs[funcname] = func
            return func
        return _add

    @classmethod
    def get(cls, funcname):
        if funcname in cls.funcs:
            return cls.funcs[funcname]
        else:
            m = "Unrecognised search term: {term}"
            raise KeyError(m.format(term=funcname))


@SearchFunction.add('exists')
def exists(key, term, index, al):
    resp = []
    for value in index.values():
        resp.extend(value)

    if term['exists']:
        return set(resp)
    else:
        return al - set(resp)
