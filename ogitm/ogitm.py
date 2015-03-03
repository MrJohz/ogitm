from . import fields

def create_init(attrs):

  def __init__(self, **kwargs):
    sets = {}
    for key, val in kwargs.items():
      if key in attrs:
        sets[key] = val
      else:
        raise ValueError("Unrecognised keyword argument {k}".format(k=key))

    for key, field in attrs.items():
      val = sets.get(key, None)

      if field.check(val):
        self.__setattr__(key, val)
      else:
        raise ValueError(
          "Value {v} failed acceptance check for key {k}".format(k=key, v=val))

  return __init__


class MetaModel(type):

  def __new__(cls, name, bases, dct):
    attrs = {}
    for key, val in dct.items():
      if isinstance(val, fields.Field):
        attrs[key] = val

    dct['_attrs'] = attrs

    if "__init__" not in dct:
      dct["__init__"] = create_init(attrs)

    print(attrs)
    return type.__new__(cls, name, bases, dct)

class Model(metaclass=MetaModel):

  def save():
    pass
