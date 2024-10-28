from enum import Enum
from tortoise.models import Model
from tortoise import fields


class User(Model):
    # __tablename__ = 'users'
    id = fields.IntField(pk=True)
    laststep = fields.TextField(default="start")
    timestamp = fields.IntField()
    username = fields.TextField(null=True)
    name = fields.TextField()
    workerid = fields.IntField(default=0)
    loh = fields.IntField(default=0)
    state = fields.IntField(null=True)
    promocode = fields.IntField(null=True)
    blocked = fields.IntField(default=0)
    selected = fields.IntField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        table = "users"


class Worker(Model):
    id = fields.IntField(pk=True)
    laststep = fields.TextField(default="start")
    roleflag = fields.IntField(default=0)
    max_discount = fields.IntField(default=0)
    margin = fields.IntField(default=70)

    class Meta:
        table = "workers"


class Promocode(Model):
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=32, unique=True)
    workerid = fields.IntField()
    discount = fields.IntField(default=3)
    cities = fields.TextField(null=True)
    sticky = fields.IntField(default=True)


class Config(Model):
    key = fields.CharField(pk=True, max_length=32)
    value = fields.TextField()

    def __str__(self):
        return self.value


class Texts(Config):
    key = fields.CharField(pk=True, max_length=32)
    value = fields.TextField()
    class Meta:
        table = "texts"


class Picture(Model):
    name = fields.CharField(pk=True, max_length=32)
    id = fields.TextField()

    def __str__(self):
        return self.id


class City(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    hidden = fields.IntField(default=0)
    areas: fields.ReverseRelation["Area"]

    def __str__(self):
        return self.name

    def __int__(self):
        return self.id

    class Meta:
        table = "cities"


class Area(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    hidden = fields.IntField(default=0)
    city: fields.ForeignKeyRelation[City] = fields.ForeignKeyField("models.City", related_name="areas")

    class Meta:
        table = "areas"


class Good(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    description = fields.TextField(null=True)
    hidden = fields.IntField(default=0)
    positions: fields.ReverseRelation["Position"]

    class Meta:
        table = 'goods'


class Position(Model):
    id = fields.IntField(pk=True)
    good: fields.ForeignKeyRelation[Good] = fields.ForeignKeyField("models.Good", related_name="positions")
    area = fields.IntField()
    price = fields.IntField()
    weight = fields.TextField()
    type = fields.TextField()
    hidden = fields.IntField(default=0)

    class Meta:
        table = 'positions'


class paySystem(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    auto = fields.IntField()

    class Meta:
        table = 'paysystems'


class paySystemConfig(Model):
    paysystemid = fields.IntField()
    key = fields.CharField(pk=True, max_length=32)
    value = fields.TextField()

    class Meta:
        table = 'paysystemconfig'


class Zalet(Model):
    id = fields.IntField(pk=True)
    userid = fields.IntField()
    workerid = fields.IntField()
    amount = fields.IntField()
    workeramount = fields.IntField(null=True)
    paysystemid = fields.IntField(null=True)
    accepted = fields.IntField(default=0)

    class Meta:
        table = 'zalets'


class Order(Model):
    id = fields.IntField(pk=True)
    userid = fields.IntField()
    workerid = fields.IntField(default=0)
    positionid = fields.IntField()
    price = fields.IntField()
    paysystemid = fields.IntField()
    invoiceid = fields.TextField(default="")

    class Meta:
        table = 'orders'
