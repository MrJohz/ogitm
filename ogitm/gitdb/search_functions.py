import json


__all__ = ['SearchFunction']


class SearchFunction:
    """A list of all search functions.

    To add a function, use the :py:meth:`.SearchFunction.add` decorator.  This
    passes the function itself through (so multiple invocations of the add
    decorator can be called on the same item), and appends it to the internal
    store of search functions.

    To get a function, use the :py:meth:`.SearchFunction.get` classmethod.
    This returns the function described by the given name, or raises KeyError
    if no function is available.

    This class should basically be used as a singleton instance - all methods
    are class methods, and operate on a shared store of data.  This probably
    isn't best practice, but it works for now.

    See :py:meth:`.SearchFunction.add` for details on what a search function
    should actually look like.
    """

    funcs = {}

    @classmethod
    def add(cls, *funcnames):
        """Add a function to the current list of functions.

        The function should have the following signature:

        :param any key: The key for which a value should be found.  This is
            usually not important - the function is also passed the index that
            pertains to this particular key.

        :param str operator: The operator/name that this function has been
            called under.  Sometimes it is simpler if different operators all
            map to the same function (for example, all string methods map to
            one function that dynamically calls the method on a string
            instance).  This can be then used to work out the specific
            operation.

        :param any argument: The argument passed to this particular operator.

        :param index: The index related to the key being searched against.
            This is basically a dict mapping every value that has been assigned
            to this key to a list of the ids of the documents where this
            key-value mapping exists.
        :type index: dict[any: list[id]]

        :param set[id] all: The set of all ids that are currently stored.
            This is useful in the case where you want to search for, say,
            non-existance of a key, in which case the set of ids that should
            be returned is the set of all ids that aren't in the index that
            the function has been passed.
        """
        def _add(func):
            for name in funcnames:
                cls.funcs[name] = func
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
def exists(key, op, arg, index, query, al):
    resp = []
    for ids in index.values():
        resp.extend(ids)

    if arg:
        return set(resp)
    else:
        return al - set(resp)


@SearchFunction.add('eq', '==', 'equal')
@SearchFunction.add('gte', '>=', 'greater-than-equal')
@SearchFunction.add('lte', '<=', 'less-than-equal')
@SearchFunction.add('lt', '<', 'less-than')
@SearchFunction.add('gt', '>', 'greater-than')
def comparison(key, op, arg, index, query, all):
    resp = []
    for value in index:
        try:
            svalue = json.loads(value)

            if op in {"gt", '>', 'greater-than'}:
                if svalue > arg:
                    resp.extend(index[value])
            elif op in {"lt", '<', 'less-than'}:
                if svalue < arg:
                    resp.extend(index[value])
            elif op in {'gte', '>=', 'greater-than-equal'}:
                if svalue >= arg:
                    resp.extend(index[value])
            elif op in {'lte', '<=', 'less-than-equal'}:
                if svalue <= arg:
                    resp.extend(index[value])
            elif op in {'eq', '==', 'equal'}:
                if svalue == arg:
                    resp.extend(index[value])
            else:  # pragma: no cover
                assert False, "Unrecognised op for comparison function: " + op

        except (ValueError, TypeError):
            continue

    return set(resp)


# TODO: expand this to other string operators?
@SearchFunction.add('startswith')
@SearchFunction.add('endswith')
@SearchFunction.add('contains')
@SearchFunction.add('isalnum')
@SearchFunction.add('isalpha')
@SearchFunction.add('isdecimal')
@SearchFunction.add('isdigit')
@SearchFunction.add('isidentifier')
@SearchFunction.add('islower')
@SearchFunction.add('isnumeric')
@SearchFunction.add('isprintable')
@SearchFunction.add('isspace')
@SearchFunction.add('istitle')
@SearchFunction.add('isupper')
def startswith(key, op, arg, index, query, all):
    resp = []
    for value in index:
        val = json.loads(value)
        try:
            if op == 'contains':
                if arg in val:
                    resp.extend(index[value])
            elif op.startswith('is'):
                if getattr(val, op)() == arg:
                    resp.extend(index[value])
            elif getattr(val, op)(arg):
                resp.extend(index[value])
        except (ValueError, TypeError, AttributeError):
            continue

    return set(resp)
