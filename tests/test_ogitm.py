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

    def test_defining_model(self, tmpdir):
        db = ogitm.gitdb.GitDB(str(tmpdir))

        class MyTest(ogitm.Model, db=db):
            name = ogitm.fields.String()
            age = ogitm.fields.Integer()

            other_fields = "Allowed as well"

        assert MyTest.other_fields == "Allowed as well"

        with pytest.raises(TypeError):

            class MyTest(ogitm.Model, db=db):
                _name = ogitm.fields.String()

        with pytest.raises(TypeError):

            class MyNewTest(ogitm.Model):
                pass

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

    def test_obj_properties(self, simple_model):
        db, TestModel = simple_model
        tm = TestModel(age=4, name="berta")
        assert tm.name == "berta"
        assert tm.age == 4

        tm.name = "Berta"
        assert tm.name == "Berta"

        with pytest.raises(ValueError):
            tm.age = "bob"

        with pytest.raises(ValueError):
            tm.name = 32

    def test_data_insertion(self, simple_model):
        db, TestModel = simple_model

        tm = TestModel(age=3)
        assert tm.name is None
        doc_id = tm.save()

        assert db.get(doc_id) == {'name': None, 'age': 3}

    def test_data_update(self, simple_model):
        db, TestModel = simple_model

        tm = TestModel(age=3)
        assert tm.name is None
        doc_id = tm.save()
        assert db.get(doc_id) == {'name': None, 'age': 3}

        tm.name = "vabble"
        assert tm.name == "vabble"
        assert doc_id == tm.save()
        assert db.get(doc_id) == {'name': 'vabble', 'age': 3}

    def test_class_instance_scoping(self, simple_model):
        db, TestModel = simple_model

        tm1 = TestModel(age=3)
        assert tm1.name is None
        assert tm1.age == 3

        tm2 = TestModel(age=18, name='Bertha')
        assert tm2.name == 'Bertha'
        assert tm2.age == 18

        assert tm1.name is None
        assert tm1.age == 3

    def test_equivalence(self, simple_model):
        db, TestModel = simple_model
        tm1 = TestModel(age=19, name="Bettie")
        tm2 = TestModel(age=25, name="Bettie")
        tm3 = TestModel(age=19, name="Brian")

        assert tm1 != tm2
        assert tm2 != tm3
        assert tm1 != tm3

        tm1.name = "Brian"
        assert tm1 == tm3
        tm3.age = 25
        tm3.name = "Bettie"
        assert tm3 == tm2

        class OtherModel(ogitm.Model, db=db):
            name = ogitm.fields.String()
            age = ogitm.fields.Integer(nullable=False)

        om = OtherModel(age=25, name="Bettie")
        assert tm3 != om
