from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String

base = declarative_base()

class Users(base):
    __tablename__ = "User"
    
    id = Column(Integer,primary_key=True,autoincrement=True)
    first_name = Column(String(100),nullable=False)
    last_name = Column(String(100),nullable=False)
    username = Column(String(100),nullable=False)
    email = Column(String(150),unique=True,nullable=False)
    password = Column(String(150),nullable=False)