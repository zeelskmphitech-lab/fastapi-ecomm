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
    
    
# buying product

class CartItem(BaseModel):
    product_id : int
    quantity : int
    
class CartResponse(BaseModel):
    cart_id : int
    user_id : int
    created_at : datetime.datetime
    is_active : bool
    items : list[CartItem]  
    model_config = ConfigDict(from_attributes=True)
    
class OrderItem(BaseModel):
    product_id : int
    quantity : int
    total_price : float
    
class OrderResponse(BaseModel):
    order_id : int
    user_id : int
    total_amount : float
    created_at : datetime.datetime
    delivery_address : str
    order_status : str
    payment_status : str
    items : list[OrderItem]
    
    model_config = ConfigDict(from_attributes=True)
    
class OrderCreate(BaseModel):
    delivery_address : str
    items : list[CartItem]
    
class OrderUpdate(BaseModel):
    delivery_address : Optional[str] = None
    order_status : Optional[str] = None
    payment_status : Optional[str] = None

class Review(BaseModel):
    product_id : int
    rating : int
    comment : Optional[str] = None
    
class Favorite(BaseModel):
    product_id : int
    