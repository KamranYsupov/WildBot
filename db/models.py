import datetime
import os

from sqlalchemy import Column, Integer, String, Float, ForeignKey, Table
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


subscription_table = Table(
    'user_subscriptions', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('product_id', Integer, ForeignKey('products.id'))
)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    subscriptions = relationship(
        'Product',
        secondary=subscription_table,
        back_populates='subscribers',
        lazy='selectin',
    )


class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    vendor_code = Column(Integer, unique=True, index=True)
    price = Column(Float)
    rating = Column(Float)
    feedbacks = Column(Integer, default=0)
    total_amount = Column(Integer)
    time_create = Column(String, default=datetime.datetime.now())


Product.subscribers = relationship(
    'User',
    secondary=subscription_table,
    back_populates='subscriptions',
    lazy='selectin',
)


