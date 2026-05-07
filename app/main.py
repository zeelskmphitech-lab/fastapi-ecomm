from fastapi import FastAPI,Depends,HTTPException
from db.database import session,engine
import models.database_models as database_models
from schemas.models import User,TokenCreate,RequestDetail,UserResponse,TokenResponse,Product,UserUpdate,UpdateProduct
from models.database_models import Users,Token,Products
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.utils import get_hashed_password,verify_password,create_access_token,create_refresh_token
from core.auth_bearer import JWTBearer,decode_jwt,JWT_SECRET_KEY, ALGORITHM
from typing import List
from datetime import datetime,timezone,timedelta
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
        print('record: ',record)
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
def get_product(dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    token = dependencies
    payload = decode_jwt(token)
    user_log_id = payload['sub']
    products=db.query(Products).filter(Products.user_id==user_log_id).all()
    if not products:
        raise HTTPException(status_code=404,detail="Product Not Found.")
    return products

@api.post('/list-product',response_model=Product)
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
def delete_product(id,dependencies=Depends(JWTBearer()),db:Session=Depends(get_db)):
    product = db.query(Products).filter(Products.product_id==id).first()
    if not product:
        raise HTTPException(status_code=404,detail="Product not Found.")
    
    db.delete(product)
    db.commit()
    return {"Product Deleted Successfully"}

# Buying products

