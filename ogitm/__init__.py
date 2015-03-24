import inflection

from . import fields
from . import gitdb


__all__ = ["Model", "ReturnSet", "MetaModel"]


def make_property(name, field):

    def getter(self):
        return self._attrs[name]

    getter.__name__ = name
    getter.__doc__ = "Getter for {name}".format(name=name)

    def setter(self, val):
        try:
            val = field.get_value(val)
        except ValueError:
            m = "Disallowed value {val} failed field checks"
            raise ValueError(m.format(val=val))

        self._attrs[name] = val

    setter.__name__ = name
    setter.__doc__ = "Setter for {name}" .format(name=name)

    return property(fget=getter, fset=setter)


def make_init(initialiser):

    def __init__(self, *args, **kwargs):
        initialiser(self, *args, **kwargs)
        if not hasattr(self, "id") or self.id is None:
            raise TypeError("This class has not been initialised")

    return __init__


class MetaModel(type):
    """Metatype for OGitM Models

    Generally, a user should subclass :py:class:`~.Model` instead of
    touching this class.  However, it is useful to be aware of the functions
    that MetaModel can perform.  Firstly, upon instantiation it removes all
    class attributes that extend :py:class:`~.fields.BaseField`, and
    assigns them to an internal dict.  It also ensures that any class that
    overrides :py:meth:`~.Model.__init__` calls the super method.  This
    makes sure that the Model should always be in a useable state.

    It also provides the :py:meth:`~.MetaModel.get_attributes` class method
    which can be used to get the data for any particular class.
    """

    _type_attributes = {}

    def __new__(meta, name, bases, dct, **kwargs):
        attrs = {}
        properties = {}
        for key, field in dct.items():
            if isinstance(field, fields.BaseField):
                if key.startswith("_"):
                    m = "Private attributes not allowed as model fields: {a}"
                    raise TypeError(m.format(a=key))
                elif key == "id":
                    m = ("'id' attribute not allowed as a field, will be "
                         "internally defined")
                    raise TypeError(m)
                attrs[key] = field
                properties[key] = make_property(key, field)
            elif key == "__init__" and callable(field):
                properties[key] = make_init(field)

        dct.update(properties)

        typ = type.__new__(meta, name, bases, dct)
        meta._type_attributes[typ] = attrs
        return typ

    def __init__(cls, name, bases, dct, **kwargs):
        db = kwargs.pop('db', None)
        if db is None and name != "Model":
            raise TypeError("Missing 'db' param.  A database must be provided")
        elif isinstance(db, str):
            db = gitdb.GitDB(db)

        table_name = kwargs.pop('table', inflection.tableize(name))
        if isinstance(db, gitdb.GitDB):
            table = db.table(table_name)
        elif isinstance(db, gitdb.Table):
            table = db
        elif name == "Model":
            table = None
        else:
            n = "Class {c}'s db parameter must be of type [str, GitDB, Table]"
            raise TypeError((n + ", not {t}").format(c=name, t=type(db)))

        super().__init__(name, bases, dct, **kwargs)

        if db is not None:
            cls._table = table

    @classmethod
    def get_attributes(cls, instance):
        """Get fields for a Model class or instance

        :param instance: An instance or class that has MetaModel
            as a metatype.
        :type instance: type or instance

        :return: Dictionary of key -> field pairs

        :raises KeyError: if the type or instance is not recognised
        """
        if isinstance(instance, type):
            return cls._type_attributes[instance]
        else:
            return cls._type_attributes[type(instance)]


class Model(metaclass=MetaModel):
    """Base class for models

    Subclass this class to declare a model.  :py:class:`~.Model` provides a
    default initialiser, an equivalence function, and the
    :py:meth:`~.Model.save` and :py:meth:`~.Model.find` methods.

    :param int model_id: If this is provided, the model will be initialised
        with the attributes specified by the document with that id in the
        database.  This is generally for internal use (i.e, creating the object
        after a search has been completed) but it may be useful.

    :param mixed kwargs: This is the more usual way of initialising the model
        - that is, by passing in key=val pairs describing the values passed to
        the fields specified by the model.  The default initialiser will then
        go through all of the arguments, check that they are known fields, and
        assign them.

    :attribute id: The instance will always have this attribute referring to
        the id that it refers to in the database.  It will be None if the
        instance has not been inserted into the database (this should never
        happen, though!)
    """

    def __init__(self, model_id=None, **kwargs):
        self._attrs = {}
        self.id = None

        if model_id is None:
            self._init_from_kwargs(kwargs)
        else:
            self.id = model_id
            self._init_from_kwargs(self._table.get(model_id), save=False)

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
            try:
                val = field.get_value(val)
            except ValueError:
                emsg = "Value {v} failed acceptance check for key {k}"
                raise ValueError(emsg.format(k=key, v=val))
            else:
                setattr(self, key, val)

        if save:
            self.save()

    def save(self):
        """Saves this instance to the database.

        If this instance has been saved before, this will update the database
        document corresponding to the current id.  Otherwise, it will insert
        a new document into the database, storing the document id.
        """
        if self.id is None:
            self.id = self._table.insert(self._attrs)
        else:
            self.id = self._table.update(self.id, self._attrs)

        return self.id

    @classmethod
    def get_table(cls):
        """Returns the table associated with this model."""
        return cls._table

    @classmethod
    def find(cls, **kwargs):
        """Finds documents in the database.

        Given keyword arguments (which have the same format as the arguments
        given to :py:meth:`.gitdb.GitDB.find`), this method returns a
        :py:class:`~.ReturnSet` containing all of the matching documents.

        :param mixed kwargs: See :py:meth:`.gitdb.GitDB.find` for the full
            finding syntax.

        :return: :py:class:`~.ReturnSet` of all of the matching documents.
        """
        for i in kwargs:
            if i not in MetaModel.get_attributes(cls):
                m = "Cannot find on attributes not owned by this class ({key})"
                raise TypeError(m.format(key=i))

        return ReturnSet(cls._table.find_ids(kwargs), cls)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        return self._attrs == other._attrs


class ReturnSet:
    """A class representing the documents returned by a particular query.

    This class can be used to further narrow down the search
    (:py:meth:`~.find`), or return initialised instances of the model that
    found them (:py:meth:`~.first`, :py:meth:`~.all`,
    :py:meth:`~.__getitem__`).  It can also tell you how many items the set
    currently contains (:py:meth:`~.__len__`)

    The documents are returned sorted in order of the ids.  This ensures that
    further operations on a set will preserve order, but should not be relied
    on, as the specifics of document ids is not part of the public interface.
    """

    def __init__(self, ids, cls):
        self.ids = sorted(ids)
        self.cls = cls

    def __len__(self):
        return len(self.ids)

    def __eq__(self, other):
        return hasattr(other, 'ids') and self.ids == other.ids

    def find(self, **kwargs):
        """Refine the terms of the original search

        Using the model that created this set, find which documents match the
        new queres, then update this set to point to the intersection of both
        the old and new queries.

        :param mixed kwargs: See :py:meth:`.Model.find`.

        :return: This set, to allow for chaining method calls.
        """
        other_ids = self.cls.find(**kwargs).ids
        self.ids = sorted(set(other_ids).intersection(self.ids))
        return self

    def first(self):
        """Returns the first document, or None"""
        if not self.ids:
            return None

        return self[0]

    def all(self):
        """Returns a list of all of the documents."""
        return [self.cls(model_id=i) for i in self.ids]

    def __getitem__(self, i):
        return self.cls(model_id=self.ids[i])
