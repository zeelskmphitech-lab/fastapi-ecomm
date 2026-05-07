from pydantic import BaseModel,EmailStr,Field,ConfigDict
from typing import Annotated,Optional,Any
import datetime

class User(BaseModel):
    first_name : str
    last_name : str
    username : str
    email : EmailStr
    password : str
    is_seller : bool
    
class UserUpdate(BaseModel):
    first_name : Optional[str] = None
    last_name : Optional[str] = None
    username : Optional[str] = None
    email : Optional[EmailStr] = None
    is_seller : Optional[bool] = None

class UserResponse(BaseModel):
    first_name : str
    last_name : str
    username : str
    email : EmailStr
    is_seller : bool

    model_config = ConfigDict(from_attributes=True)
    
class TokenCreate(BaseModel):
    user_id:int
    access_token:str
    refresh_token:str
    is_active:bool
    created_at:datetime.datetime

class RequestDetail(BaseModel):
    email : EmailStr
    password : str
    
class TokenResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str

    model_config = ConfigDict(from_attributes=True)
    
class Product(BaseModel):
    product_name:str
    product_description:str
    product_price:float
    product_stoke:int
    
class UpdateProduct(BaseModel):
    product_name:Optional[str] = None
    product_description:Optional[str] = None
    product_price:Optional[float] = None
    product_stoke:Optional[int] = None