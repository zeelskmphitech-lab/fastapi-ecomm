from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
import datetime

class UserCreate(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    password: str
    is_seller: Optional[bool] = False

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    is_seller: Optional[bool] = None

class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    username: str
    email: EmailStr
    is_seller: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    user: UserResponse
    access_token: str
    refresh_token: str

    model_config = ConfigDict(from_attributes=True)

class ProductCreate(BaseModel):
    product_name: str
    product_description: str
    product_price: float
    product_stoke: int
    category: Optional[str] = None

class ProductUpdate(BaseModel):
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    product_price: Optional[float] = None
    product_stoke: Optional[int] = None
    category: Optional[str] = None

class ProductResponse(BaseModel):
    product_id: int
    user_id: int
    product_name: str
    product_description: str
    product_price: float
    product_stoke: int
    category: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class CartItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0)

class CartItemResponse(BaseModel):
    cartitem_id: int
    cart_id: int
    product_id: int
    quantity: int
    total_price: float

    model_config = ConfigDict(from_attributes=True)

class CartResponse(BaseModel):
    cart_id: int
    user_id: int
    created_at: datetime.datetime
    is_active: bool
    items: List[CartItemResponse]

    model_config = ConfigDict(from_attributes=True)

class OrderCreate(BaseModel):
    delivery_address: str

class OrderItemResponse(BaseModel):
    orderitem_id: int
    order_id: int
    product_id: int
    quantity: int
    total_price: float

    model_config = ConfigDict(from_attributes=True)

class OrderResponse(BaseModel):
    order_id: int
    user_id: int
    total_amount: float
    created_at: datetime.datetime
    delivery_address: str
    order_status: str
    payment_status: str
    items: List[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)

class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None

class ReviewResponse(BaseModel):
    review_id: int
    user_id: int
    product_id: int
    rating: int
    comment: Optional[str] = None
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class FavoriteCreate(BaseModel):
    product_id: int

class FavoriteResponse(BaseModel):
    favorite_id: int
    user_id: int
    product_id: int
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
