from abc import ABC

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import TypeDecorator

import sqlalchemy
import json

db = SQLAlchemy()


class DictType(TypeDecorator, ABC):
    impl = sqlalchemy.Text()

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class User(db.Model):
    discord_id = db.Column(db.String)
    basket = db.Column(DictType)
    wii_id = db.Column(db.Integer, primary_key=True, unique=True)
    auth_token = db.Column(db.String)
    auth_key = db.Column(db.String)
    roo_uid = db.Column(db.String)
    payment_id = db.Column(db.String)
