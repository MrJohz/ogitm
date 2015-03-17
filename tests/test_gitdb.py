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

        with pytest.raises(ValueError):
            gdb.update(312991, {'one': 'three'})

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

    def test_searching_empty(self, gdb):
        assert gdb.find({'circle': True}) == []

    def test_find_one(self, gdb):
        gdb.insert({'a': 1})
        gdb.insert({'a': 'b'})
        gdb.insert({'a': 'c'})
        id_4 = gdb.insert({'a': True})

        assert gdb.find_one({'a': True}) == (id_4, {'a': True})
        assert gdb.find_one({'a': {'exists': True}}) is not None
        assert gdb.find_one({'a': 'non-existant'}) is None

    def test_find_items(self, gdb):
        gdb.insert({'a': 1})
        gdb.insert({'a': 'b'})
        gdb.insert({'a': 'c'})

        assert gdb.find_items({'a': 1}) == [{'a': 1}]
        assert len(gdb.find_items({'a': {'exists': True}})) == 3
        assert gdb.find_items({'a': 'non-existant'}) == []

    def test_creating_tables(self, gdb):
        # Syntax 1
        t1 = gdb.table('test-table')
        # Syntax 2
        t2 = gdb['test-table']

        assert t1 == t2
        assert t1 != gdb['test-table-new-name']

    def test_using_default_table(self, gdb):
        t1 = gdb[gitdb.DEFAULT_TABLE]
        assert t1 == gdb.default_table

        doc = gdb.insert({'alpha': 'beta', 'gamma': 1})
        assert t1.get(doc) == {'alpha': 'beta', 'gamma': 1}

    def test_failed_tables(self, gdb):
        with pytest.raises(ValueError):
            gdb['__meta__']

    def test_dropping_tables(self, gdb):
        t1 = gdb['test-table']
        t1.insert({'alpha': 'beta', 'gamma': 1})
        assert len(t1.find({'alpha': 'beta'})) == 1
        gdb.drop('test-table')
        t2 = gdb['test-table']
        assert len(t2.find({'alpha': 'beta'})) == 0

    def test_failed_drops(self, gdb):
        with pytest.raises(ValueError):
            gdb.drop('__meta__')

        with pytest.raises(ValueError):
            gdb.drop(gitdb.DEFAULT_TABLE)

        with pytest.raises(ValueError):
            gdb.drop('this table does not exist at all')

        gdb.drop('this table does not exist at all', force=True)


class TestSearchFunctions:

    @pytest.fixture
    def gdb(self, tmpdir):
        g = gitdb.GitDB(str(tmpdir))
        g.insert({'int': -42})
        g.insert({'int': 1})
        g.insert({'int': 12})
        g.insert({'int': 123})
        g.insert({'str': 'hello'})
        g.insert({'str': 'goodbye'})
        g.insert({'bool': False})
        g.insert({'bool': True})
        g.insert({'str': 'for-bool', 'bool': True})
        return g

    def test_exists(self, gdb):
        assert len(gdb.find_items({'int': {'exists': True}})) == 4
        assert len(gdb.find_items({'int': {'exists': False}})) == 5
        assert len(gdb.find_items({
            'bool': {'exists': True},
            'str': {'exists': False}
            })) == 2
        assert gdb.find_items({
            'bool': {'exists': True},
            'str': 'for-bool'
            }) == [{'str': 'for-bool', 'bool': True}]

    def test_operators(self, gdb):
        assert gdb.find_items({'int': {'gt': 14}}) == [{'int': 123}]
        assert len(gdb.find_items({'int': {'lt': 4}})) == 2
        assert len(gdb.find_items({'int': {'gte': 124}})) == 0
        assert len(gdb.find_items({'int': {'gte': 123}})) == 1
        assert len(gdb.find_items({'int': {'gte': 122}})) == 1
        assert len(gdb.find_items({'int': {'lte': 122}})) == 3

        assert len(gdb.find_items({'str': {'lt': 'h'}})) == 2
        assert len(gdb.find_items({'str': {'gte': 'f'}})) == 3

        assert len(gdb.find_items({'bool': {'eq': False}})) == 1
        assert len(gdb.find_items({'bool': {'gt': 'hello'}})) == 0

    def test_string_funcs(self, gdb):
        assert gdb.find_items({'str': {'endswith': 'ye'}}) == \
            [{'str': 'goodbye'}]
        assert gdb.find_items({'str': {'startswith': 'h'}}) == \
            [{'str': 'hello'}]
        assert gdb.find_items({'int': {'startswith': 3}}) == \
            []
        assert gdb.find_items({'str': {'contains': 'll'}}) == \
            [{'str': 'hello'}]
        assert len(gdb.find_items({'str': {'isalpha': True}})) == 2
        assert len(gdb.find_items({'str': {'isalpha': False}})) == 1

    def test_nonexistent_key(self, gdb):
        with pytest.raises(KeyError):
            gdb.find({'str': {'this search does not exist': 4}})
