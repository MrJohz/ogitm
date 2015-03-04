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

    def test_saving_data(self, gittree):
        gittree['doo-dah'] = 'yabadabadoo'
        gittree.save()

        assert gittree['doo-dah'] == 'yabadabadoo'
        assert gittree.get('doo-dah') == 'yabadabadoo'
        del gittree['doo-dah']
        with pytest.raises(KeyError):
            gittree['doo-dah']
        assert gittree.get('doo-dah') is None

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
