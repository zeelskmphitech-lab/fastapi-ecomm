from pydantic import BaseModel,EmailStr,Field
from typing import Annotated,Optional,Any
import datetime

class User(BaseModel):
    first_name : str
    last_name : str
    username : str
    email : EmailStr
    password : str
    
class TokenCreate(BaseModel):
    user_id:int
    access_token:str
    refresh_token:str
    is_active:bool
    created_at:datetime.datetime

class RequestDetail(BaseModel):
    email : EmailStr
    password : str
    