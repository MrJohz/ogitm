import ogitm

class MyModel(ogitm.Model):
  name = ogitm.fields.String(regex="s.*")
  age = ogitm.fields.Integer(nullable=False)
  has_legs = ogitm.fields.Boolean()
  gender = ogitm.fields.Choice(choices=["male", "female"])
