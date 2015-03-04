from ogitm import gitdb

def test_gitdb(tmpdir):
  gitdb.GitDB(str(tmpdir))
