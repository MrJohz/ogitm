from ogitm.gitdb.json_wrapper import JsonDictWrapper


class TestTreeWrapper:

    def test_instantiation(self):
        d = dict()
        assert JsonDictWrapper(d).unwrap() is d

    def test_attributes(self):
        d = {'hello': '1'}
        wrapped = JsonDictWrapper(d)
        assert wrapped['hello'] == 1
        wrapped['goodbye'] = "hello"
        assert d['goodbye'] == '"hello"'
        assert len(d) == len(wrapped) == 2
        del d['goodbye']
        assert 'goodbye' not in wrapped
        del wrapped['hello']
        assert 'hello' not in d
        wrapped['hello'] = 'goodbye'
        for i in wrapped:
            assert i in d
