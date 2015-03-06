from ogitm import gitdb
import pytest


class TestGitDB:

    @pytest.fixture
    def gdb(self, tmpdir):
        return gitdb.GitDB(str(tmpdir))

    def test_instantiation(self, tmpdir):
        gdb = gitdb.GitDB(str(tmpdir))
        assert gdb

    def test_insertion(self, gdb):
        doc_id = gdb.insert({'one': 'two'})
        assert gdb.get(doc_id) == {'one': 'two'}
        with pytest.raises(TypeError):
            gdb.get(None)

    def test_update(self, gdb):
        doc_id = gdb.insert({'one': 'two'})
        assert gdb.get(doc_id) == {'one': 'two'}

        gdb.update(doc_id, {'one': 'three'})
        assert gdb.get(doc_id) == {'one': 'three'}

        gdb.update(doc_id, {'seven': 'eight'})
        assert gdb.get(doc_id) == {'seven': 'eight'}
        assert gdb.find({'one': {'exists': True}}) == []

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
        id_1 = gdb.insert({'square': True, 'circle': False})
        gdb.insert({'circle': True, 'square': False})
        id_3 = gdb.insert({'circle': False, 'square': False, 'triangle': True})
        assert (gdb.find({'square': True}) ==
                [(id_1, {'square': True, 'circle': False})])
        assert gdb.find({'triangle': False}) == []
        assert ((id_1, {'circle': False, 'square': True})
                in gdb.find({'circle': False}))
        assert ((id_3, {'circle': False, 'square': False, 'triangle': True})
                in gdb.find({'circle': False}))
        assert len(gdb.find({'circle': False})) == 2
        assert gdb.find({'none': False}) == []

    def test_searching_complex(self, gdb):
        id_1 = gdb.insert({'square': True, 'circle': False})
        id_2 = gdb.insert({'circle': True, 'square': False})
        id_3 = gdb.insert({'circle': False, 'square': False, 'triangle': True})
        assert (gdb.find_ids({'triangle': {'exists': True}}) == [id_3])

        assert id_1 in gdb.find_ids({'triangle': {'exists': False}})
        assert id_2 in gdb.find_ids({'triangle': {'exists': False}})

        with pytest.raises(KeyError):
            gdb.find({'triangle': {'this search does not exist': 4}})

    def test_search_numeric(self, gdb):
        bob = gdb.insert({'name': 'bob', 'age': 42})
        geoff = gdb.insert({'name': 'geoff', 'age': 64})
        jeremy = gdb.insert({'name': 'jeremy', 'age': 12})
        cristoff = gdb.insert({'name': 'cristoff', 'age': 42})

        assert (gdb.find({'age': {'gt': 60}}) ==
                [(geoff, {'name': 'geoff', 'age': 64})])

        assert (gdb.find({'age': {'gt': 'this will not work'}}) == [])

        assert bob in gdb.find_ids({'age': {'lt': 60}})
        assert jeremy in gdb.find_ids({'age': {'lt': 60}})
        assert cristoff in gdb.find_ids({'age': {'lt': 60}})
        assert len(gdb.find_ids({'age': {'lt': 60}})) == 3

        assert len(gdb.find({'age': {'gte': 64}})) == 1
        assert len(gdb.find({'age': {'lte': 10}})) == 0
        assert len(gdb.find({'age': {'less-than-equal': 14}})) == 1
        assert len(gdb.find({'age': {'<=': 12}})) == 1
        assert len(gdb.find({'age': {'==': 42}})) == 2

    def test_search_other_types(self, gdb):  # pragma: no flakes
        aard = gdb.insert({'word': 'aardvark'})
        abac = gdb.insert({'word': 'abacus'})
        gdb.insert({'word': 'xylophone'})

        b_int = gdb.insert({'bogon': 11623})
        b_bol = gdb.insert({'bogon': False})
        b_str = gdb.insert({'bogon': 'str'})

        assert gdb.find({'word': {'gt': 'zylophone'}}) == []
        assert gdb.find_ids({'word': {'eq': 'abacus'}}) == [abac]

        assert aard in gdb.find_ids({'word': {'lt': 'xenu'}})
        assert abac in gdb.find_ids({'word': {'lt': 'xenu'}})
        assert len(gdb.find({'word': {'lt': 'xenu'}})) == 2

        assert gdb.find_ids({'bogon': {'eq': 'str'}}) == [b_str]
        assert gdb.find_ids({'bogon': {'eq': False}}) == [b_bol]
        assert gdb.find_ids({'bogon': {'gt': 10000}}) == [b_int]

    def test_find_one(self, gdb):
        gdb.insert({'a': 1})
        gdb.insert({'a': 'b'})
        gdb.insert({'a': 'c'})
        id_4 = gdb.insert({'a': True})

        assert gdb.find_one({'a': True}) == (id_4, {'a': True})
        assert gdb.find_one({'a': {'exists': True}}) is not None
        assert gdb.find_one({'a': 'non-existant'}) is None
