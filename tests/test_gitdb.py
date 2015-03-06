from ogitm import gitdb
import pytest


class TestGitDB:

    @pytest.fixture
    def gdb(self, tmpdir):
        return gitdb.GitDB(str(tmpdir))

    def test_instantiation(self, tmpdir):
        gdb = gitdb.GitDB(str(tmpdir))
        assert gdb

    def test_insertion_removal(self, gdb):
        doc_id = gdb.insert({'one': 'two'})
        assert gdb.get(doc_id) == {'one': 'two'}

    def test_multiple_inserts(self, gdb):
        doc1 = gdb.insert({'one': 'two'})
        doc2 = gdb.insert({'three': 'four'})
        assert gdb.get(doc1) == {'one': 'two'}
        assert gdb.get(doc2) == {'three': 'four'}

    def test_multiple_instances(self, tmpdir):
        g1 = self.gdb(tmpdir)
        g2 = self.gdb(tmpdir)

        doc1 = g1.insert({'a': 'b'})
        assert g2.get(doc1) == {'a': 'b'}

        doc2 = g2.insert({'c': 'd'})
        assert g1.get(doc2) == {'c': 'd'}

        assert doc1 != doc2

    def test_transaction(self, tmpdir):
        g1 = self.gdb(tmpdir)
        g2 = self.gdb(tmpdir)

        assert not g1.transaction_open
        assert not g2.transaction_open
        g1.insert({'one': 'two'})
        assert not g1.transaction_open
        assert not g2.transaction_open

        g1.begin_transaction()
        assert g1.transaction_open
        assert not g2.transaction_open
        i1 = g1.insert({'one': 'two'})
        with pytest.raises(ValueError):
            g2.get(i1)
        g1.commit()
        assert g2.get(i1) == {'one': 'two'}

        g1.begin_transaction()
        i2 = g1.insert({'three': 'four'})
        with pytest.raises(ValueError):
            g2.get(i2)
        g1.rollback()
        with pytest.raises(ValueError):
            g2.get(i2)

        with g2.transaction():
            i3 = g2.insert({'five': 'six'})
            assert g2.transaction_open
            assert not g1.transaction_open
            with pytest.raises(ValueError):
                g1.get(i3)

        assert g2.get(i3) == {'five': 'six'}

        with pytest.raises(AssertionError):
            with g2.transaction():
                i4 = g2.insert({'seven': 'eight'})
                raise AssertionError('Thrown deliberately')

        with pytest.raises(ValueError):
            g1.get(i4)

        g1.begin_transaction()
        with pytest.raises(ValueError):
            g1.begin_transaction()
        g1.rollback()

        with pytest.raises(ValueError):
            g2.commit()
        with pytest.raises(ValueError):
            g2.rollback()

        with g1.transaction():
            with pytest.raises(ValueError):
                g1.begin_transaction()
            with pytest.raises(ValueError):
                g1.commit()
            with pytest.raises(ValueError):
                g1.rollback()

    def test_searching_simple(self, gdb):
        gdb.insert({'square': True, 'circle': False})
        gdb.insert({'circle': True, 'square': False})
        gdb.insert({'circle': False, 'square': False, 'triangle': True})
        assert (gdb.find({'square': True}) ==
                [{'square': True, 'circle': False}])
        assert gdb.find({'triangle': False}) == []
        assert {'circle': False, 'square': True} in gdb.find({'circle': False})
        assert ({'circle': False, 'square': False, 'triangle': True}
                in gdb.find({'circle': False}))
        assert len(gdb.find({'circle': False})) == 2
        assert gdb.find({'none': False}) == []

    def test_searching_complex(self, gdb):
        gdb.insert({'square': True, 'circle': False})
        gdb.insert({'circle': True, 'square': False})
        gdb.insert({'circle': False, 'square': False, 'triangle': True})
        assert (gdb.find({'triangle': {'exists': True}}) ==
                [{'circle': False, 'square': False, 'triangle': True}])

        assert ({'square': True, 'circle': False}
                in gdb.find({'triangle': {'exists': False}}))
        assert ({'circle': True, 'square': False}
                in gdb.find({'triangle': {'exists': False}}))

        with pytest.raises(KeyError):
            gdb.find({'triangle': {'this search does not exist': 4}})

    def test_search_numeric(self, gdb):
        gdb.insert({'name': 'bob', 'age': 42})
        gdb.insert({'name': 'geoff', 'age': 64})
        gdb.insert({'name': 'jeremy', 'age': 12})
        gdb.insert({'name': 'cristoff', 'age': 42})

        assert (gdb.find({'age': {'gt': 60}}) ==
                [{'name': 'geoff', 'age': 64}])

        assert (gdb.find({'age': {'gt': 'this will not work'}}) == [])

        assert {'name': 'bob', 'age': 42} in gdb.find({'age': {'lt': 60}})
        assert {'name': 'jeremy', 'age': 12} in gdb.find({'age': {'lt': 60}})
        assert {'name': 'cristoff', 'age': 42} in gdb.find({'age': {'lt': 60}})
        assert len(gdb.find({'age': {'lt': 60}})) == 3

        assert len(gdb.find({'age': {'gte': 64}})) == 1
        assert len(gdb.find({'age': {'lte': 10}})) == 0
        assert len(gdb.find({'age': {'less-than-equal': 14}})) == 1
        assert len(gdb.find({'age': {'<=': 12}})) == 1
        assert len(gdb.find({'age': {'==': 42}})) == 2
