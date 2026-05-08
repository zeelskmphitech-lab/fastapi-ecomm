from fastapi import FastAPI,Depends,HTTPException
from db.database import session,engine
import models.database_models as database_models
from schemas.models import User,TokenCreate,RequestDetail,UserResponse,TokenResponse,Product,UserUpdate,UpdateProduct,CartItem
from models.database_models import OrderItems, Orders, Users,Token,Products,Carts,CartItems
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.utils import get_hashed_password,verify_password,create_access_token,create_refresh_token
from core.auth_bearer import JWTBearer,decode_jwt,JWT_SECRET_KEY, ALGORITHM
from typing import List
from datetime import datetime,timedelta
from jwt import decode
from core.auth_bearer import token_required
from sqlalchemy import update

api = FastAPI()


database_models.base.metadata.create_all(bind=engine)

def get_db():
    db=session()
    try:
        yield db
    finally:
        db.close()
    
@api.get("/users/",response_model=List[UserResponse])
@token_required
def get_users(dependencies=Depends(JWTBearer()),db:Session= Depends(get_db)):
    user = db.query(Users).all()
    return user

@api.post("/register/",status_code=201,response_model=TokenResponse)
def add_user(user:User,db:Session=Depends(get_db)):
    is_email_exists =db.query(Users).filter(Users.email==user.email).first()
    hashed_password = get_hashed_password(user.password)
    new_user = Users(first_name=user.first_name,last_name=user.last_name,username=user.username,email=user.email,password=hashed_password)
    
    if is_email_exists:
        raise HTTPException(status_code=409,detail="Email Already registered.")
    else:
        access_token = create_access_token(new_user.id)
        refresh_token = create_refresh_token(new_user.id)
       
        token = Token(user_id=new_user.id,access_token=access_token,refresh_token=refresh_token,is_active=True)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        db.add(token)
        db.commit()
        db.refresh(token) 

        return {"user":new_user,"access_token":access_token,"refresh_token":refresh_token}
    
    
@api.put('/update-account/{id}',response_model=UserUpdate)
@token_required
def update_user(id,user_update:UserUpdate,db:Session=Depends(get_db)): 
    user = db.query(Users).filter(Users.id == id).first()
    if not user:
        raise HTTPException(detail="User not found",status_code=404)
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

@api.post('/login/',response_model=TokenResponse)
def user_login(request : RequestDetail,db:Session=Depends(get_db)):
    user = db.query(Users).filter(Users.email==request.email).first()
    user_id=db.query(Users.id).where(Users.email==request.email)
    
    if user is None:
        raise HTTPException(status_code=400,detail='Invalid email.')
    hashed_password = user.password
    if not verify_password(request.password,hashed_password):
        raise HTTPException(status_code=400,detail='Invalid password.')
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    token = Token(user_id=user.id,access_token=access_token,refresh_token=refresh_token,is_active=True)
    
    db.add(token)
    db.commit()
    db.refresh(token)
    return {"user":user,"access_token":access_token,"refresh_token":refresh_token}

@api.post('/logout')
def logout(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    token_record = db.query(Token).all()
    info=[]
    
    for record in token_record:
        now = datetime.now().replace(tzinfo=None)
        if (now-record.created_at) > timedelta(days=1):
            info.append(record.user_id)
        
    if info:
        existing_token = db.query(Token).where(Token.user_id.in_(info)).delete()
        db.commit()
        
    existing_token = db.query(Token).filter(Token.user_id==user_id,Token.access_token==token).first()
    if existing_token:
        existing_token.is_active = False
        db.add(existing_token)
        db.commit()
        db.refresh(existing_token)
        return {"message":"User Logged Out Successfully."}

# products

@api.get('/see-product',response_model=List[Product])
@token_required
def get_product(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_log_id = payload['sub']
    products=db.query(Products).filter(Products.user_id==user_log_id).all()
    if not products:
        raise HTTPException(status_code=404,detail="Product Not Found.")
    return products

@api.post('/list-product',response_model=Product)
@token_required
def add_product(product:Product,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_log_id = payload['sub']
    new_product = Products(user_id=user_log_id,product_name=product.product_name,product_description=product.product_description,product_price=product.product_price,product_stoke=product.product_stoke)
    is_seller = db.query(Users.is_seller).where(Users.id==user_log_id)
    
    if product.product_stoke <= 0:
        raise HTTPException(status_code=400,detail="Product Stoke has to be atleast 1.")
    
    if is_seller:
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        return new_product
    else:
        raise HTTPException(status_code=404,detail='Become Seller for listing product.')
    
@api.put('/update-product/{id}',response_model=Product)
@token_required
def update_product(id,product:UpdateProduct,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    myproduct = db.query(Products).filter(Products.product_id==id).first()
    if not myproduct:
        raise HTTPException(status_code=404, detail="Product not found.")
    updated_product = product.model_dump(exclude_unset=True)
    
    for key,value in updated_product.items():
        setattr(myproduct,key,value)
        
    db.commit()
    db.refresh(myproduct)
    
    return myproduct

@api.delete('/delete-product/{id}')
@token_required
def delete_product(id,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    product = db.query(Products).filter(Products.product_id==id).first()
    if not product:
        raise HTTPException(status_code=404,detail="Product not Found.")
    
    db.delete(product)
    db.commit()
    return {"Product Deleted Successfully"}

# Buying products

@api.post('/cart/')
@token_required
def create_cart(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_log_id = payload['sub']
    
    newcart=Carts(user_id = user_log_id,is_active = True)
    db.add(newcart)
    db.commit()
    db.refresh(newcart)
    return {"Cart Created, now you can add products into cart."}

@api.post('/add_to_cart/')
@token_required
def add_to_cart(cartitem:CartItem,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_log_id = payload['sub']
    cart = db.query(Carts).filter(Carts.user_id==user_log_id,Carts.is_active==True).first()
    if not cart:
        newcart=Carts(user_id = user_log_id,is_active = True)
        db.add(newcart)
        db.commit()
        db.refresh(newcart)

    product = db.query(Products).filter(Products.product_id==cartitem.product_id).first()
    if not product:
        raise HTTPException(status_code=404,detail="Product Not Found")
    
    price = product.product_price
    total_price = price * cartitem.quantity
    new_item_cart = CartItems(user_id=int(user_log_id),cart_id = cart.cart_id,product_id=cartitem.product_id,quantity=cartitem.quantity,total_price=total_price)
    
    db.add(new_item_cart)
    db.commit()
    db.refresh(new_item_cart)
    
    return {"Product Add To cart Successfully."}


@api.get('/cart_items/',response_model=List[CartItem])
@token_required
def get_cart_items(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_log_id = payload['sub']
    cart = db.query(Carts).filter(Carts.user_id==user_log_id,Carts.is_active==True).first()
    if not cart:
        raise HTTPException(status_code=404,detail="Cart Not Found.")
    
    items = db.query(CartItems).filter(CartItems.cart_id==cart.cart_id).all()
    return items

@api.delete('/remove_cart_item/{id}')
@token_required 
def remove_cart_item(id,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_log_id = payload['sub']
    cart = db.query(Carts).filter(Carts.user_id==user_log_id,Carts.is_active==True).first()
    if not cart:
        raise HTTPException(status_code=404,detail="Cart Not Found.")
    
    item = db.query(CartItems).filter(CartItems.cartitem_id==id,CartItems.cart_id==cart.cart_id).first()
    if not item:
        raise HTTPException(status_code=404,detail="Cart Item Not Found.")
    
    db.delete(item)
    db.commit()
    
    return {"Cart Item Removed Successfully."}

@api.delete('/clear_cart/')
@token_required
def clear_cart(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_log_id = payload['sub']
    cart = db.query(Carts).filter(Carts.user_id==user_log_id,Carts.is_active==True).first()
    if not cart:
        raise HTTPException(status_code=404,detail="Cart Not Found.")
    
    items = db.query(CartItems).filter(CartItems.cart_id==cart.cart_id).all()
    for item in items:
        db.delete(item)
    db.commit()
    
    return {"Cart Cleared Successfully."}

@api.post('/checkout/')
@token_required
def checkout(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_log_id = payload['sub']
    cart = db.query(Carts).filter(Carts.user_id==user_log_id,Carts.is_active==True).first()
    if not cart:
        raise HTTPException(status_code=404,detail="Cart Not Found.")
    
    items = db.query(CartItems).filter(CartItems.cart_id==cart.cart_id).all()
    if not items:
        raise HTTPException(status_code=404,detail="No Items in Cart to Checkout.")
    
    for item in items:
        product = db.query(Products).filter(Products.product_id==item.product_id).first()
        if product.product_stoke < item.quantity:
            raise HTTPException(status_code=400,detail=f"Not enough stock for product {product.product_name}.")
        product.product_stoke -= item.quantity
        db.add(product)
    
    snapshot = db.query(CartItems).filter(CartItems.cart_id==cart.cart_id).all()
    
    cart.is_active = False
    db.add(cart)
    db.commit()
    
    return {"Checkout Successful. Thank you for your purchase!"}

@api.post('/refresh-token/',response_model=TokenResponse)
def refresh_token(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    
    token_record = db.query(Token).filter(Token.user_id==user_id,Token.refresh_token==token,is_active=True).first()
    
    if not token_record:
        raise HTTPException(status_code=401,detail="Invalid refresh token.")
    
    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    
    token_record.access_token = new_access_token
    token_record.refresh_token = new_refresh_token
    db.add(token_record)
    db.commit()
    db.refresh(token_record)
    
    user = db.query(Users).filter(Users.id==user_id).first()
    
    return {"user":user,"access_token":new_access_token,"refresh_token":new_refresh_token}

@api.post('/become-seller/')
@token_required
def become_seller(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    
    user = db.query(Users).filter(Users.id==user_id).first()
    if not user:
        raise HTTPException(status_code=404,detail="User Not Found.")
    
    user.is_seller = True
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return {"message":"Congratulations! You are now a seller."}

@api.post('/review-product/{id}')
@token_required
def review_product(id,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    
    product = db.query(Products).filter(Products.product_id==id).first()
    if not product:
        raise HTTPException(status_code=404,detail="Product Not Found.")
    
    return {"message":"Thank you for reviewing the product!"}

@api.post('/rate-product/{id}')
@token_required
def rate_product(id,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    
    product = db.query(Products).filter(Products.product_id==id).first()
    if not product:
        raise HTTPException(status_code=404,detail="Product Not Found.")
    
    return {"message":"Thank you for rating the product!"}

@api.post('/search-product/')
@token_required
def search_product(query:str,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    
    products = db.query(Products).filter(Products.product_name.ilike(f"%{query}%")).all()
    if not products:
        raise HTTPException(status_code=404,detail="No Products Found.")
    
    return products

@api.get('/product/{id}',response_model=Product)
@token_required
def get_product_by_id(id,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    
    product = db.query(Products).filter(Products.product_id==id).first()
    if not product:
        raise HTTPException(status_code=404,detail="Product Not Found.")
    
    return product

@api.post('/place-order/')
@token_required
def place_order(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    
    cart = db.query(Carts).filter(Carts.user_id==user_id,Carts.is_active==True).first()
    if not cart:
        raise HTTPException(status_code=404,detail="Cart Not Found.")
    
    items = db.query(CartItems).filter(CartItems.cart_id==cart.cart_id).all()
    if not items:
        raise HTTPException(status_code=404,detail="No Items in Cart to Place Order.")
    
    total_amount = sum(item.total_price for item in items)
    
    order = Orders(user_id=user_id,total_amount=total_amount,delivery_address="123 Main St")
    db.add(order)
    db.commit()
    db.refresh(order)
    
    for item in items:
        order_item = OrderItems(order_id=order.order_id,product_id=item.product_id,quantity=item.quantity,total_price=item.total_price)
        db.add(order_item)
    
    cart.is_active = False
    db.add(cart)
    
    db.commit()
    
    return {"message":"Order Placed Successfully!"}

@api.get('/order/{id}')
@token_required
def get_order_by_id(id,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_id = payload['sub']
    
    order = db.query(Orders).filter(Orders.order_id==id,Orders.user_id==user_id).first()
    if not order:
        raise HTTPException(status_code=404,detail="Order Not Found.")
    
    order_items = db.query(OrderItems).filter(OrderItems.order_id==order.order_id).all()
    
    return {"order":order,"items":order_items}