import abc
import re
import types
import numbers

ALWAYS_SUCCESSFUL_RE = types.SimpleNamespace()
ALWAYS_SUCCESSFUL_RE.search = lambda *args, **kwargs: True

NULL_SENTINEL = object()


class BaseField(abc.ABC):

    """Abstract Base Class for field types.

    Cannot be instantiated, but should be inherited to provide all the
    useful information that a field might need.

    Arguments:

      default (any) -- A default value to provide if the input is ever
        None.  If not provided, and nullable is False, a field will
        not accept None as an argument.

      nullable (bool) -- True if this field can be None/null, False
        otherwise.  Defaults to True.

      coerce (func x: x) -- A function that can coerce any input into
        input of a valid type.  If it cannot coerce, it should either
        return "False" or raise a ValueError.  Defaults to a no-op.
        e.g. `coerce=int` would convert values to int where possible.
    """

    def __init__(self, **kwargs):
        # pass-through by default
        self.coerce_func = kwargs.pop('coerce', lambda x: x)

        self.default = kwargs.pop('default', NULL_SENTINEL)
        self.nullable = kwargs.pop('nullable', True)
        self._accept_none = self.nullable or \
            (self.default is not NULL_SENTINEL)

        if len(kwargs) > 0:
            msg = "Unrecognised parameter(s) passed to field: {d}"
            raise TypeError(msg.format(d=kwargs))

    @abc.abstractmethod
    def check(self, val):
        """Base case method to check if a value is allowed by this field.

        Must be overriden.  Currently only returns True, but may do its
        own checking in future, and so should probably be checked before
        any overriden method.

        Arguments:

          val (any) -- Value to check.

        Returns (bool) -- Whether that value is allowed by the parameters
            given to this field.
        """
        return True

    def coerce(self, val):
        """Attempt to coerce a value using the pre-defined function.

        If no function was passed in, the default operation is to
        return the value straight through.  If the function fails to
        coerce (i.e. raises ValueError), the value is returned
        unchanged.  (`type_check` should therefore always be used to
        check the type of a coerced value.)

        Arguments:

          val (any) -- Value to coerce

        Returns (any) -- Coerced value
        """
        try:
            return self.coerce_func(val)
        except ValueError:
            return val

    def type_check(self, val, typ=None):
        """Check if value is of a certain type (using nullability).

        If this field instance can be nulled, checks if the val is
        either of type `typ` or of the None type.  Otherwise, it just
        checks if the val is of type `typ`.  Note that `typ` is passed
        straight through to `isinstance`, so it can be any value allowed
        by the second parameter of `isinstance`.

        Arguments:

          val (any) -- Value to check
          typ (type | Tuple[type]) -- Type(s) to check against

        Returns (bool) -- Whether val is of type typ.
        """
        if typ is None:  # just check nullability
            return self._accept_none or val is not None

        if self._accept_none:
            return isinstance(val, typ) or val is None
        else:
            return isinstance(val, typ)


class String(BaseField):

    def __init__(self, **kwargs):
        regex = kwargs.pop('regex', None)
        super().__init__(**kwargs)

        if regex is None:
            self.regex = ALWAYS_SUCCESSFUL_RE
        elif isinstance(regex, str):
            self.regex = re.compile(regex)
        else:
            self.regex = regex

    def check(self, val):
        if not super().check(val):  # pragma: no cover
            return False

        val = self.coerce(val)
        if not self.type_check(val, str):
            return False

        if self.regex is not None and val is not None:
            return self.regex.search(val) is not None

        return True


class Number(BaseField):
    # NOTE: more specifically, *real* numbers

    def __init__(self, **kwargs):
        self.min = kwargs.pop('min', None)
        self.max = kwargs.pop('max', None)
        super().__init__(**kwargs)

    def check(self, val):
        if not super().check(val):  # pragma: no cover
            return False

        val = self.coerce(val)
        if not self.type_check(val, numbers.Real):
            return False

        if self.min is not None and val < self.min:
            return False

        if self.max is not None and val > self.max:
            return False

        return True


class Integer(Number):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def check(self, val):
        if not super().check(val):
            return False

        val = self.coerce(val)
        # NOTE: booleans are ints.  This is bad, but there's nothing really
        # that can be done about it.  :(
        if not self.type_check(val, int) or isinstance(val, bool):
            return False

        return True


class Float(Number):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def check(self, val):
        if not super().check(val):
            return False

        val = self.coerce(val)
        if not self.type_check(val, float):
            return False

        return True


BOOLEAN_TRUE = ("yes", "y", "true", "t", "on")
BOOLEAN_FALSE = ("no", "n", "false", "f", "off")


def coerce_boolean(val):
    if isinstance(val, str):
        if val.lower() in BOOLEAN_TRUE:
            return True
        elif val.lower() in BOOLEAN_FALSE:
            return False

    ival = int(val)  # will raise ValueError if impossible
    if ival == 1:
        return True
    elif ival == 0:
        return False
    else:
        raise ValueError("Could not coerce {val}".format(val=val))


class Boolean(BaseField):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def check(self, val):
        if not super().check(val):  # pragma: no cover
            return False

        val = self.coerce(val)
        if not self.type_check(val, (bool, int)):
            return False
        if val is not None and int(val) not in (0, 1):
            return False

        return True


class Choice(BaseField):

    def __init__(self, choices=None, **kwargs):
        if choices is None:
            try:
                self.choices = kwargs.pop('choices')
            except KeyError:
                raise TypeError("Choice type requires 'choices' parameter")
        else:
            self.choices = choices

        super().__init__(**kwargs)

        for item in self.choices:
            if self.coerce(item) != item:
                msg = "Coercion func prevents selecting item {i} from choices"
                raise TypeError(msg.format(i=item))

    def check(self, val):
        if not super().check(val):  # pragma: no cover
            return False

        val = self.coerce(val)
        if not self.type_check(val):
            return False

        if val not in self.choices:
            if not (self.nullable and val is None):
                return False

        return True
