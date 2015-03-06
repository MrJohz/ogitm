from . import fields
from . import gitdb  # pragma: no flakes


def make_property(name, field):

    def getter(self):
        return self._attrs[name]

    getter.__name__ = name
    getter.__doc__ = "Getter for {name}".format(name=name)

    def setter(self, val):
        if not field.check(val):
            m = "Unallowed value {val} failed field checks"
            raise ValueError(m.format(val=val))

        self._attrs[name] = val

    setter.__name__ = name
    setter.__doc__ = "Setter for {name}" .format(name=name)

    return property(fget=getter, fset=setter)


class MetaModel(type):

    type_attributes = {}

    def __new__(meta, name, bases, dct, db=None):
        attrs = {}
        properties = {}
        for key, val in dct.items():
            if isinstance(val, fields.BaseField):
                if key.startswith("_"):
                    m = "Private attributes not allowed as model fields: {a}"
                    raise TypeError(m.format(a=key))
                attrs[key] = val
                properties[key] = make_property(key, val)

        dct.update(properties)

        typ = type.__new__(meta, name, bases, dct)
        meta.type_attributes[typ] = attrs
        return typ

    def __init__(cls, name, bases, dct, db=None):
        if db is None and name != "Model":
            raise TypeError("Missing 'db' param.  A database must be provided")
        cls._db = db

    @classmethod
    def get_attributes(cls, instance):
        return cls.type_attributes[instance.__class__]


class Model(metaclass=MetaModel):

    def __init__(self, **kwargs):
        self._attrs = {}
        self._id = None

        to_set = {}
        attrs = MetaModel.get_attributes(self)

        for key, val in kwargs.items():
            if key in attrs:
                to_set[key] = val
            else:
                emsg = "Unrecognised keyword argument {k}".format(k=key)
                raise ValueError(emsg)

        for key, field in attrs.items():
            val = to_set.get(key, None)
            if field.check(val):
                setattr(self, key, val)
            else:
                emsg = "Value {v} failed acceptance check for key {k}"
                raise ValueError(emsg.format(k=key, v=val))

    def save(self):
        if self._id is None:
            self._id = self._db.insert(self._attrs)
        else:
            pass

        return self._id
