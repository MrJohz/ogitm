import pytest
from ogitm import fields


class TestBaseField:

  def test_non_instantiable(self):
    with pytest.raises(TypeError):
      fields.BaseField()


class TestStringField:

  def test_bare_instantiation(self):
    sf = fields.String()
    assert sf.check("Any string input at all")
    assert not sf.check(42), "Integer input"
    assert not sf.check(False), "Boolean input"

  def test_nullable(self):
    sf = fields.String(nullable=False)
    assert sf.check("Not none")
    assert not sf.check(None)
    sf = fields.String(nullable=True)
    assert sf.check(None)

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
