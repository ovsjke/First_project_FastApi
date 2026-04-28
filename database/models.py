from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

"""
Описание всех таблиц в БД
"""


class Group(Base):
    __tablename__ = "group"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    teacher_id = Column(Integer)
    soft_delete = Column(Integer, default=0)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    role = Column(String)  # "admin", "teacher", "student"
    login = Column(String, unique=True)
    password = Column(String)
    group_id = Column(Integer, ForeignKey("group.id"))
    soft_delete = Column(Integer, default=0)


class Test(Base):
    __tablename__ = "test"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    group_id = Column(Integer, ForeignKey("group.id"))
    max_attemp = Column(Integer)
    soft_delete = Column(Integer, default=0)


class Question(Base):
    __tablename__ = "question"
    id = Column(Integer, primary_key=True)
    test_id = Column(Integer, ForeignKey("test.id"))
    description = Column(String)
    point = Column(Integer)
    answer = Column(String)
    soft_delete = Column(Integer, default=0)


class Attempt(Base):
    __tablename__ = "attempt"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    test_id = Column(Integer, ForeignKey("test.id"))
    result = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)


class ActionLog(Base):
    __tablename__ = "log"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    method = Column(String)
    path = Column(String)
    status_code = Column(Integer)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
