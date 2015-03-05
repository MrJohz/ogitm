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

    @pytest.mark.xfail
    def test_searching_complex(self, gdb):
        gdb.insert({'square': True, 'circle': False})
        gdb.insert({'circle': True, 'square': False})
        gdb.insert({'circle': False, 'square': False, 'triangle': True})
        assert (gdb.find({'triangle': {'exists': True}}) ==
                [{'circle': False, 'square': False, 'triangle': True}])
