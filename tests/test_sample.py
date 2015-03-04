import pytest
from . import sample


def test_model():
    s = sample.MyModel(age=3)
    s = sample.MyModel(name="sam", age=3)
    with pytest.raises(ValueError):
        s = sample.MyModel(nonname=None, age=3)
        s = sample.MyModel(name="bob", age=3)
        s = sample.MyModel(name="sam")
