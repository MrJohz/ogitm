import pygit2 as pg2
import json

class GitDB:

  AUTHOR = pg2.Signature('-', '-')
  COMMITTER = pg2.Signature('-', '-')

  def _get_next_id(self):
    if hasattr(self, "_id"):
      self._id += 1
    else:
      self._id = 0

    return self._id

  def __init__(self, location):
    self.repo = pg2.init_repository(location, bare=True)
    if self.repo.is_empty:
      self.current_tree = self.repo.TreeBuilder()
    else:
      self.current_tree = self.repo.TreeBuilder()
    self.current_tree = self.repo.TreeBuilder()

  def insert(self, document):
    d_id = self._get_next_id()
    txt = json.dumps(document, indent=2)
    d_oid = self.repo.create_blob(txt)
    self.current_tree.insert(str(d_id), d_oid, pg2.GIT_FILEMODE_BLOB)

    self.save('insert ' + str(d_id))

    return doc_id

  def save(self, msg='-'):
    tree_id = self.current_tree.write()
    commit_id = self.repo.create_commit(
      'master', self.AUTHOR, self.COMMITTER,
      msg, tree_id, [])
    self.current_tree = self.repo.TreeBuilder()


