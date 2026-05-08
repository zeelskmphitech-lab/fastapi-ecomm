from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column,Integer,String,Boolean,DateTime,ForeignKey,Float
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
    
class Carts(base):
    __tablename__ = "Cart"
    cart_id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer, ForeignKey("User.id"), nullable=False)
    created_at = Column(DateTime,default=datetime.datetime.now)
    is_active = Column(Boolean,default=True)
    
class CartItems(base):
    __tablename__ = "CartItem"
    cartitem_id = Column(Integer,primary_key=True,autoincrement=True)
    user_id = Column(Integer ,ForeignKey("User.id"), nullable=False)
    cart_id = Column(Integer,ForeignKey("Cart.cart_id"), nullable=False)
    product_id = Column(Integer,ForeignKey("Product.product_id"), nullable=False)
    quantity = Column(Integer,default=1)
    total_price = Column(Float)
    
class Orders(base):
    __tablename__ = "Order"
    order_id = Column(Integer,primary_key=True,autoincrement=True)
    user_id = Column(Integer,ForeignKey("User.id"), nullable=False)
    total_amount = Column(Float,nullable=False)     
    created_at = Column(DateTime,default=datetime.datetime.now)
    delivery_address = Column(String(500),nullable=False)
    order_status = Column(String(50),default="Pending")
    payment_status = Column(String(50),default="Pending")

class OrderItems(base):
    __tablename__ = "OrderItem"
    orderitem_id = Column(Integer,primary_key=True,autoincrement=True)
    order_id = Column(Integer,ForeignKey("Order.order_id"), nullable=False)
    product_id = Column(Integer,ForeignKey("Product.product_id"), nullable=False)
    quantity = Column(Integer,default=1)
    total_price = Column(Float)
    
class Reviews(base):
    __tablename__ = "Review"
    review_id = Column(Integer,primary_key=True,autoincrement=True)
    user_id = Column(Integer,ForeignKey("User.id"), nullable=False)
    product_id = Column(Integer,ForeignKey("Product.product_id"), nullable=False)
    rating = Column(Integer,nullable=False)
    comment = Column(String(500))
    created_at = Column(DateTime,default=datetime.datetime.now)
    
class Favorites(base):
    __tablename__ = "Favorite"
    favorite_id = Column(Integer,primary_key=True,autoincrement=True)
    user_id = Column(Integer,ForeignKey("User.id"), nullable=False)
    product_id = Column(Integer,ForeignKey("Product.product_id"), nullable=False)
    created_at = Column(DateTime,default=datetime.datetime.now)
    
