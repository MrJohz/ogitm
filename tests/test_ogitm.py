import ogitm
import pytest


class TestOGitM:

    @pytest.fixture
    def simple_model(self, tmpdir):
        db = ogitm.gitdb.GitDB(str(tmpdir))

        class TestModel(ogitm.Model, db=db):
            name = ogitm.fields.String()
            age = ogitm.fields.Integer(nullable=False)

        return db, TestModel

    def test_instantiation(self, simple_model):
        db, TestModel = simple_model

        tm = TestModel(age=3)
        assert tm.age == 3
        assert tm.name is None

        tm = TestModel(name="Tom", age=24)
        assert tm.age == 24
        assert tm.name == "Tom"

        with pytest.raises(ValueError):
            TestModel(non_param="", age=24, name="str")

        with pytest.raises(ValueError):
            TestModel(age="invalid-type", name=34)

        with pytest.raises(ValueError):
            TestModel(name="note-no-age")

    def test_data_insertion(self, simple_model):
        db, TestModel = simple_model

        tm = TestModel(age=3)
        assert tm.name is None
        doc_id = tm.save()

        assert db.get(doc_id) == {'name': None, 'age': 3}
