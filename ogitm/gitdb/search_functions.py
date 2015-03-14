import json


class SearchFunction:

    funcs = {}

    @classmethod
    def add(cls, *funcnames):
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
            elif getattr(val, op)(arg):
                resp.extend(index[value])
        except (ValueError, TypeError, AttributeError):
            continue

    return set(resp)
