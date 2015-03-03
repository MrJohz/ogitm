import abc
import re

class _AlwaysSuccessfulRe:
  def search(*args, **kwargs):
    return True

class BaseField(abc.ABC):

  def __init__(self, **kwargs):
    self.nullable = kwargs.pop('nullable', True)
    self.coerce_func = kwargs.pop('coerce', lambda x: x) # pass-through by default

    if len(kwargs) > 0:
      raise TypeError("Too many paramaters passed to field")

  @abc.abstractmethod
  def check(self, val):
    return True

  def coerce(self, val):
    try:
      return self.coerce_func(val)
    except ValueError:
      return val

  def type_check(self, val, typ):
    if self.nullable or val is not None:
      return isinstance(val, typ) or isinstance(val, type(None))
    else:
      return isinstance(val, typ)

class String(BaseField):

  def __init__(self, **kwargs):
    regex = kwargs.pop('regex', None)
    super().__init__(**kwargs)

    if regex is None:
      self.regex = _AlwaysSuccessfulRe()
    elif isinstance(regex, str):
      self.regex = re.compile(regex)
    else:
      self.regex = regex

  def check(self, val):
    if not super().check(val):
      return False

    val = self.coerce(val)
    if not self.type_check(val, str):
      return False

    if self.regex is not None and val is not None:
      return self.regex.search(val) is not None

    return True

class Integer(BaseField):

  def __init__(self, **kwargs):
    self.min = kwargs.pop('min', None)
    self.max = kwargs.pop('max', None)
    super().__init__(**kwargs)

  def check(self, val):
    if not super().check(val):
      return False

    val = self.coerce(val)
    # NOTE: booleans are ints.  This is bad, but there's nothing really
    # that can be done about it.  :(
    if not self.type_check(val, int) or isinstance(val, bool):
      return False

    if self.min is not None:
      if val < self.min:
        return False

    if self.max is not None:
      if val > self.max:
        return False

    return True
