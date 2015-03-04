import pytest
from . import sample


def test_model():
    sample.MyModel(age=3)
    sample.MyModel(name="sam", age=3)
    with pytest.raises(ValueError):
        sample.MyModel(nonname=None, age=3)
        sample.MyModel(name="bob", age=3)
        sample.MyModel(name="sam")
