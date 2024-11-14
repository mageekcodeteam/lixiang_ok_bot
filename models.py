from peewee import Model, SqliteDatabase, TextField, FloatField, CharField, IntegerField, DateTimeField, ForeignKeyField, BooleanField
from flask_login import UserMixin

db = SqliteDatabase('db.db')


class BaseModel(Model):
    class Meta:
        database = db


class Forbidden_words(BaseModel):
    word = TextField(unique=True)


class User(BaseModel):
    user_id = IntegerField(unique=True)
    username = TextField()
    number_of_messages = IntegerField()
    status = TextField()
    last_activity = TextField()
    warnings = IntegerField()


class Statistics(BaseModel):
    one_day = IntegerField(default=0)
    seven_day = IntegerField(default=0)
    thirty_day = IntegerField(default=0)


class Statistics_ban(BaseModel):
    one_day = IntegerField(default=0)
    seven_day = IntegerField(default=0)
    thirty_day = IntegerField(default=0)


class Statistics_mut(BaseModel):
    one_day = IntegerField(default=0)
    seven_day = IntegerField(default=0)
    thirty_day = IntegerField(default=0)


class Statistics_new_user(BaseModel):
    one_day = IntegerField(default=0)
    seven_day = IntegerField(default=0)
    thirty_day = IntegerField(default=0)


class Statistics_exit_user(BaseModel):
    one_day = IntegerField(default=0)
    seven_day = IntegerField(default=0)
    thirty_day = IntegerField(default=0)


class Const(BaseModel):
    warnings = IntegerField(default=0)
    time_for_block = IntegerField(default=1)
    chat_id = TextField(default=0)


class SupportChat(BaseModel):
    user_id = IntegerField()
    username = CharField()
    subject = TextField()
    last_message_time = DateTimeField()
    status = CharField()


class SupportMessage(BaseModel):
    support_chat = ForeignKeyField(SupportChat, backref='messages')
    role = CharField()
    message = TextField()
    timestamp = DateTimeField()


class UserBanInfo(BaseModel):
    user_id = IntegerField()
    timestamp = DateTimeField()


class UserMutInfo(BaseModel):
    user_id = IntegerField()
    timestamp = DateTimeField()


class Admin(UserMixin, BaseModel):
    username = TextField(unique=True)
    password = TextField()


class BanInfo(BaseModel):
    user_id = IntegerField()
    message = TextField()


db.create_tables([Forbidden_words, User, Statistics, Const, SupportChat, SupportMessage, UserBanInfo,
                 UserMutInfo, Admin, BanInfo, Statistics_ban, Statistics_mut, Statistics_new_user, Statistics_exit_user])
