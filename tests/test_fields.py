import pytest
from ogitm import fields

# TODO: Number test (should take max/min from Integer)
# TODO: Choice coersion, type-check tests


class TestBaseField:

    def test_non_instantiable(self):
        with pytest.raises(TypeError):
            fields.BaseField()

    def test_invalid_names(self):
        with pytest.raises(TypeError):
            fields.String(unrecognised_filed=False)

    def test_wrong_coercion(self):
        sf = fields.String(coerce=int)
        assert sf.check("Hello")  # TODO: is this right?
        assert not sf.check("522")
        assert not sf.check(52)

    def test_nullable(self):
        sf = fields.String(nullable=False)
        assert sf.check("Not none")
        assert not sf.check(None)
        assert not sf.check(False)
        sf = fields.String(nullable=True)
        assert sf.check("Not none")
        assert sf.check(None)
        assert not sf.check(False)


class TestStringField:

    def test_bare_instantiation(self):
        sf = fields.String()
        assert sf.check("Any string input at all")
        assert not sf.check(42), "Integer input"
        assert not sf.check(False), "Boolean input"

    def test_coerce(self):
        sf = fields.String(coerce=str)
        assert sf.check("String input should still go through")
        assert sf.check(42), "So should integer input"
        assert sf.check(True), "Eveen boolean input"

    def test_regex_str_input(self):
        sf = fields.String(regex=r'^start.*$')
        assert sf.check("start blah blah blah")
        assert not sf.check("no start blah blah blah")

    def test_regex_re_input(self):
        import re
        sf = fields.String(regex=re.compile(r'^start.*$'))
        assert sf.check("start blah blah blah")
        assert not sf.check("not start blah blah blah")

    def test_regex_and_coerce(self):
        sf = fields.String(coerce=str, regex='^2$')
        assert sf.check("2")
        assert sf.check(2)
        assert not sf.check("3")
        assert not sf.check(22)


class TestIntegerField:

    def test_bare_instantiation(self):
        sf = fields.Integer()
        assert sf.check(34)
        assert not sf.check(3.4)
        assert not sf.check("hello")
        assert not sf.check(True)

    def test_coerce_with_failure(self):
        sf = fields.Integer(coerce=int)
        assert sf.check("42")
        assert sf.check(42)
        assert sf.check(3.4)
        assert not sf.check("4.5")
        assert not sf.check("hello")

    def test_minimum(self):
        sf = fields.Integer(min=3)
        assert sf.check(100)
        assert sf.check(3)
        assert not sf.check(1)

    def test_maximum(self):
        sf = fields.Integer(max=4)
        assert sf.check(-100)
        assert sf.check(4)
        assert not sf.check(100)


class TestFloatField:

    def test_bare_instantiation(self):
        sf = fields.Float()
        assert sf.check(3.4)
        assert sf.check(34.0)
        assert not sf.check("hello")
        assert not sf.check("3.5")

    def test_coersion(self):
        sf = fields.Float(coerce=float)
        assert sf.check(3.4)
        assert sf.check(34)
        assert sf.check(".4")
        assert not sf.check("hello")


class TestBooleanField:

    def test_bare_instantiation(self):
        sf = fields.Boolean()
        assert sf.check(True)
        assert sf.check(False)
        assert sf.check(1)
        assert sf.check(0)
        assert not sf.check(34)
        assert not sf.check(1.0)
        assert not sf.check("True")
        assert not sf.check("False")
        assert not sf.check("HJAKSDHJKAS")

    def test_boolean_coersion(self):
        sf = fields.Boolean(coerce=fields.coerce_boolean)
        assert sf.check(True)
        assert sf.check(False)
        assert sf.check("True")
        assert sf.check("t")
        assert sf.check("false")
        assert sf.check("F")
        assert sf.check("on")
        assert sf.check("off")
        assert sf.check("yes")
        assert sf.check("y")
        assert sf.check("no")
        assert sf.check("n")
        assert sf.check("trUE")
        assert not sf.check("hello")
        assert not sf.check("0.2")
        assert not sf.check(42.0)

    def test_nullable(self):
        sf = fields.Boolean()
        assert sf.check(None)
        sf = fields.Boolean(nullable=False)
        assert not sf.check(None)


class TestChoiceField:

    def test_bare_instantiation(self):
        sf = fields.Choice(choices=["1", "goodbye"])
        assert sf.check("1")
        assert sf.check("goodbye")
        assert not sf.check("Neither of those")
        assert not sf.check(1)
        with pytest.raises(ValueError):
            sf = fields.Choice()

    def test_nullable(self):
        sf = fields.Choice(choices=["hello", "goodbye"])
        assert sf.check(None)
        sf = fields.Choice(choices=["hello", "goodbye"], nullable=True)
        assert sf.check(None)
        sf = fields.Choice(choices=["hello", "goodbye"], nullable=False)
        assert not sf.check(None)
