import datetime
import os

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    vendor_code = Column(Integer, unique=True, index=True)
    price = Column(Float)
    rating = Column(Float)
    feedbacks = Column(Integer, default=0)
    total_amount = Column(Integer)
    time_create = Column(String, default=str(datetime.datetime.now()))




