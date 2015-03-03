import abc
import re

class _AlwaysSuccessfulRe:
  def search(*args, **kwargs):
    return True

class Field(abc.ABC):

  def __init__(self, **kwargs):
    self.nullable = kwargs.pop('nullable', True)

    if len(kwargs) > 0:
      raise TypeError("Too many paramaters passed to field")

  @abc.abstractmethod
  def check(self, val):
    return self.nullable or val is not None

class String(Field):

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

    if self.regex is not None and val is not None:
      return self.regex.search(val) is not None

    return True

class Integer(Field):

  def __init__(self, **kwargs):
    self.min = kwargs.pop('min', None)
    self.max = kwargs.pop('max', None)
    super().__init__(**kwargs)

  def check(self, val):
    if self.min is not None:
      if val < self.min:
        return False

    if self.max is not None:
      if val > self.max:
        return False

    return super().check(val)
