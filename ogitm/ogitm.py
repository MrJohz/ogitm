from . import fields


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
                elif key == "id":
                    m = ("'id' attribute not allowed as a field, will be "
                         "internally defined")
                    raise TypeError(m)
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
        return cls.type_attributes[type(instance)]


class Model(metaclass=MetaModel):

    def __init__(self, **kwargs):
        self._attrs = {}
        self.id = None

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

        self.save()

    def save(self):
        if self.id is None:
            self.id = self._db.insert(self._attrs)
        else:
            self.id = self._db.update(self.id, self._attrs)

        return self.id

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self._attrs == other._attrs
