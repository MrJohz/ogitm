import abc
import re
import numbers

from .compat import SimpleNamespace

__all__ = ['BaseField', 'String', 'Number', 'Float', 'Integer',
           'Boolean', 'coerce_boolean', 'Choice']

ALWAYS_SUCCESSFUL_RE = SimpleNamespace()
ALWAYS_SUCCESSFUL_RE.search = lambda *args, **kwargs: True

NULL_SENTINEL = object()


class BaseField(metaclass=abc.ABCMeta):

    """Abstract Base Class for field types.

    Cannot be instantiated, but should be inherited to provide all the
    useful information that a field might need.

    :param any default:  A default value to provide if the input is ever
        None.  If not provided, and nullable is False, a field will
        not accept None as an argument.

    :param bool nullable:  True if this field can be None/null, False
        otherwise.  Defaults to True.

    :param coerce:  A function that can coerce any input into
        input of a valid type.  If it cannot coerce, it should either
        return "False" or raise a ValueError.  Defaults to a no-op.

        Example:  ``coerce=int`` would convert values to int where possible.
    """

    def __init__(self, **kwargs):
        # pass-through by default
        self.coerce_func = kwargs.pop('coerce', lambda x: x)

        self.default = kwargs.pop('default', NULL_SENTINEL)
        self._has_default = self.default is not NULL_SENTINEL
        self.nullable = kwargs.pop('nullable', not self._has_default)
        self._accept_none = self.nullable

        if len(kwargs) > 0:
            msg = "Unrecognised parameter(s) passed to field: {d}"
            raise TypeError(msg.format(d=kwargs))

    @abc.abstractmethod
    def check(self, val):
        """Base case method to check if a value is allowed by this field.

        Must be overriden.  Currently only returns True, but may do its
        own checking in future, and so should probably be checked before
        any overriden method.

        :param any val: Value to check

        :return: Whether that value is allowed by the parameters given to this
            field.
        """
        return True

    def get_value(self, val):
        if not self.check(val) and not self._has_default:
            raise ValueError("Invalid value {d} with no default".format(d=val))

        if self.check(val):
            return val
        else:
            return self.default

    def coerce(self, val):
        """Attempt to coerce a value using the pre-defined function.

        If no function was passed in, the default operation is to
        return the value straight through.  If the function fails to
        coerce (i.e. raises ValueError), the value is returned
        unchanged.  (`type_check` should therefore always be used to
        check the type of a coerced value.)

        :param any val: Value to coerce

        :return: Coerced value
        """
        try:
            return self.coerce_func(val)
        except ValueError:
            return val

    def type_check(self, val, typ=None):
        """Check if value is of a certain type (using nullability).

        If this field instance can be nulled, checks if the val is
        either of type ``typ`` or of the None type.  Otherwise, it just
        checks if the val is of type ``typ``.  Note that ``typ`` is passed
        straight through to ``isinstance``, so it can be any value allowed
        by the second parameter of ``isinstance``.

        :param any val:  Value to check
        :param typ: Type(s) to check against

        :return: Whether val is of type ``typ``.
        """
        if typ is None:  # just check nullability
            return self._accept_none or val is not None

        if self._accept_none:
            return isinstance(val, typ) or val is None
        else:
            return isinstance(val, typ)


class String(BaseField):
    """A field representing string types.

    :param regex: Regular expression that this string must match.
        If not present, any string will match.  Can be either a regular
        expression object, or a string.
    :type regex: string or regex
    """

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
    """A field representing real numeric types.

    :param numeric min: The minimum (inclusive) value that this field can
        contain.  If not specified, there is no minimum.
    :param numeric max: The maximum (inclusive) value that this field can
        contain.  If not specified, there is no maximum.
    """

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
    """A field representing integers.

    :param numeric min: See :py:class:`.Number`
    :param numeric max: See :py:class:`.Number`
    """

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
    """A field representing floating point numbers.

    :param numeric min: See :py:class:`.Number`
    :param numeric max: See :py:class:`.Number`
    """

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
    """A useful function for coercing various types to boolean.

    Unlike the usual Python :py:func:`bool` function which simply tests if a
    value is empty, this matches boolean ``True``, strings in the set
    ``{'yes', 'y', 'true', 't', 'on'}`` and the integer ``1`` for ``True``,
    or boolean ``False``, strings in the set
    ``{'no', 'n', 'false', 'f', 'off'}`` and the integer ``0`` for ``False``.

    This is done in a case-insensitive manner.  If the value is a string not in
    the described sets, a number that doesn't equal ``1`` or ``0``, or any
    other type (excepting :py:class:`boolean` of course), this function will
    raise :py:class:`ValueError`.
    """
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
    """A field representing boolean values

    See :py:func:`.coerce_boolean` for a useful coercion function for this
    field."""

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
    """A field representing a single item from a set of items.

    :param collection choices: A required collection of items.  The check
        method will then ensure that the value must be in this collection.
    """

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
