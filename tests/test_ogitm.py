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

        class MyOtherTest(ogitm.Model, db=str(tmpdir)):
            name = ogitm.fields.String()
            age = ogitm.fields.Integer()

        assert MyTest.other_fields == "Allowed as well"

        with pytest.raises(TypeError):

            class _0(ogitm.Model, db=db):
                id = ogitm.fields.String()

        with pytest.raises(TypeError):

            class _1(ogitm.Model, db=db):
                _name = ogitm.fields.String()

        with pytest.raises(TypeError):

            class _2(ogitm.Model):
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

    def test_finding(self, simple_model):
        db, TestModel = simple_model
        tm1 = TestModel(age=25, name="Bettie")
        tm2 = TestModel(age=19, name="Brian")
        TestModel(age=19, name="Bettie")

        result = TestModel.find(age=25)
        assert len(result) == 1
        assert result.first() == tm1
        assert result.all() == [tm1]

        with pytest.raises(TypeError):
            TestModel.find(not_an_attribute=500)

        result = TestModel.find(age=19)
        assert len(result) == 2

        new_result = result.find(name="Brian")
        assert new_result is result
        assert len(result) == 1
        assert result.first() == tm2
        assert result.all() == [tm2]

        assert len(TestModel.find(age={"exists": True})) == 3
        assert len(TestModel.find(age=1000)) == 0

        assert TestModel.find(age=1000).first() is None
