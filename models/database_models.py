from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String,Boolean,DateTime,ForeignKey
import datetime

base = declarative_base()

class Users(base):
    __tablename__ = "User"
    id = Column(Integer,primary_key=True,autoincrement=True)
    first_name = Column(String(100),nullable=False)
    last_name = Column(String(100),nullable=False)
    username = Column(String(100),nullable=False)
    email = Column(String(150),unique=True,nullable=False)
    password = Column(String(255),nullable=False)
    is_seller = Column(Boolean,default=False)
    
class Token(base):
    __tablename__ = 'Token'
    user_id = Column(Integer, ForeignKey("User.id"))
    access_token = Column(String(500),nullable=False,primary_key=True)
    refresh_token = Column(String(500),nullable=False)
    is_active = Column(Boolean)
    created_at = Column(DateTime,default=datetime.datetime.now)
    
class Products(base):
    __tablename__ ="Product"
    user_id = Column(Integer, ForeignKey("User.id"))
    product_id = Column(Integer,primary_key=True,autoincrement=True)
    product_name = Column(String(100),nullable=False)
    product_description = Column(String(1200),nullable=False)
    product_price = Column(Integer,nullable=False)
    product_stoke = Column(Integer,nullable=False)