from ogitm import gitdb
import pygit2
import pytest


class TestTreeWrapper:

    @pytest.fixture
    def gittree(self, tmpdir):
        git = pygit2.init_repository(str(tmpdir), bare=True)
        return gitdb.TreeWrapper(git)

    def test_instantiation(self, tmpdir):
        git = pygit2.init_repository(str(tmpdir), bare=True)
        tree = gitdb.TreeWrapper(git)
        assert tree

    def test_inserting_and_removing(self, gittree):
        gittree['name'] = 'text'
        assert gittree['name'] == 'text'
        assert gittree.get('name') == 'text'
        del gittree['name']
        with pytest.raises(KeyError):
            gittree['name']
        assert gittree.get('name') is None

    def test_clear(self, gittree):
        gittree['bob'] = 'Joe Bloggs'
        assert gittree['bob'] == 'Joe Bloggs'
        gittree.clear()
        assert gittree.get('bob') is None
        with pytest.raises(KeyError):
            gittree['bob']

        gittree['bob'] = 'Joe Bloggs'
        gittree.save()
        assert gittree['bob'] == 'Joe Bloggs'
        gittree.clear()
        assert gittree.get('bob') is None
        assert 'bob' not in gittree
        with pytest.raises(KeyError):
            gittree['bob']

    def test_saving_data(self, gittree):
        gittree['doo-dah'] = 'yabadabadoo'
        gittree.save()
        gittree.save()

        assert gittree['doo-dah'] == 'yabadabadoo'
        assert gittree.get('doo-dah') == 'yabadabadoo'
        del gittree['doo-dah']
        with pytest.raises(KeyError):
            gittree['doo-dah']
        assert gittree.get('doo-dah') is None

    def test_contains(self, gittree):
        gittree['brainfart'] = 'boabab'
        assert gittree['brainfart'] == 'boabab'
        assert 'brainfart' in gittree
        assert 'carrot' not in gittree

        gittree.save()

        assert 'brainfart' in gittree
        assert 'carrot' not in gittree

    def test_saving_over_multiple_instances(self, tmpdir):
        tree = self.gittree(tmpdir)
        tree['gaggle'] = 'baggle'
        tree.save()

        tree2 = self.gittree(tmpdir)
        assert tree2['gaggle'] == 'baggle'
        assert tree2.get('gaggle') == 'baggle'
        del tree2['gaggle']
        with pytest.raises(KeyError):
            tree2['gaggle']
        assert tree2.get('gaggle') is None

    def test_deletion_save(self, tmpdir):
        tree = self.gittree(tmpdir)
        tree['boggle'] = 'goggle'
        tree.save()
        assert tree['boggle'] == 'goggle'

        del tree['boggle']
        with pytest.raises(KeyError):
            tree['boggle']

        tree.save()
        with pytest.raises(KeyError):
            tree['boggle']

        tree2 = self.gittree(tmpdir)
        with pytest.raises(KeyError):
            tree2['boggle']


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

    @pytest.mark.xfail
    def test_searching_complex(self, gdb):
        gdb.insert({'square': True, 'circle': False})
        gdb.insert({'circle': True, 'square': False})
        gdb.insert({'circle': False, 'square': False, 'triangle': True})
        assert (gdb.find({'triangle': {'exists': True}}) ==
                [{'circle': False, 'square': False, 'triangle': True}])
