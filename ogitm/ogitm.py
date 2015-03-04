from . import fields


class MetaModel(type):

    type_attributes = {}

    def __new__(cls, name, bases, dct):
        attrs = {}
        for key, val in dct.items():
            if isinstance(val, fields.BaseField):
                attrs[key] = val

        typ = type.__new__(cls, name, bases, dct)
        cls.type_attributes[typ] = attrs
        return typ

    @classmethod
    def get_attributes(cls, instance):
        return cls.type_attributes[instance.__class__]


class Model(metaclass=MetaModel):

    def __init__(self, **kwargs):
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

    def save():
        pass
