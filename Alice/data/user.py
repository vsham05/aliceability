import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    
    user_id = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    Alices_wins = sqlalchemy.Column(sqlalchemy.Integer, server_default='0')
    users_wins = sqlalchemy.Column(sqlalchemy.Integer, server_default='0')
    Alices_wins_not_hints = sqlalchemy.Column(sqlalchemy.Integer, server_default='0')
    users_wins_not_hints = sqlalchemy.Column(sqlalchemy.Integer, server_default='0')
    score = sqlalchemy.Column(sqlalchemy.Integer, server_default='0')

