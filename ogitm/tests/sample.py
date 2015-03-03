import ogitm

class MyModel(ogitm.Model):
  name = ogitm.String(regex="s.*")
  age = ogitm.Integer(nullable=False)
  #has_legs = ogitm.Boolean()
  #gender = ogitm.Choice("male", "female")
