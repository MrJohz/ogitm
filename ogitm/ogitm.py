from . import fields
from . import gitdb


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

        if isinstance(db, str):
            db = gitdb.GitDB(db)

        cls._db = db

    @classmethod
    def get_attributes(cls, instance):
        if isinstance(instance, type):
            return cls.type_attributes[instance]
        else:
            return cls.type_attributes[type(instance)]


class Model(metaclass=MetaModel):

    def __init__(self, model_id=None, **kwargs):
        self._attrs = {}
        self.id = None

        if model_id is None:
            self._init_from_kwargs(kwargs)
        else:
            self.id = model_id
            self._init_from_kwargs(self._db.get(model_id), save=False)

        assert self.id is not None

    def _init_from_kwargs(self, kwargs, save=True):
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

        if save:
            self.save()

    def save(self):
        if self.id is None:
            self.id = self._db.insert(self._attrs)
        else:
            self.id = self._db.update(self.id, self._attrs)

        return self.id

    @classmethod
    def find(cls, **kwargs):
        for i in kwargs:
            if i not in MetaModel.get_attributes(cls):
                m = "Cannot find on attributes not owned by this class ({key})"
                raise TypeError(m.format(key=i))

        return ReturnSet(cls._db.find_ids(kwargs), cls)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self._attrs == other._attrs


class ReturnSet:

    def __init__(self, ids, cls):
        self.ids = sorted(ids)
        self.cls = cls

    def __len__(self):
        return len(self.ids)

    def find(self, **kwargs):
        other_ids = self.cls.find(**kwargs).ids
        self.ids = sorted(set(other_ids).intersection(self.ids))
        return self

    def first(self):
        if not self.ids:
            return None

        return self[0]

    def all(self):
        return [self.cls(model_id=i) for i in self.ids]

    def __getitem__(self, i):
        return self.cls(model_id=self.ids[i])
