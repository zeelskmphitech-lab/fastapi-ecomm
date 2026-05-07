from fastapi import FastAPI,Depends,HTTPException
from db.database import session,engine
import models.database_models as database_models
from schemas.models import User,TokenCreate,RequestDetail,UserResponse,TokenResponse
from models.database_models import Users,Token
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.utils import get_hashed_password,verify_password,create_access_token,create_refresh_token
from core.auth_bearer import JWTBearer,decode_jwt,JWT_SECRET_KEY, ALGORITHM
from typing import List
from datetime import datetime,timezone,timedelta
from jwt import decode
from core.auth_bearer import token_required

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
    
@api.post('/login/',response_model=TokenResponse)
def user_login(request : RequestDetail,db:Session=Depends(get_db)):
    user = db.query(Users).filter(Users.email==request.email).first()
    user_id=db.query(Users.id).where(Users.email==request.email)
    is_logged_in = db.query(Token).filter(Token.user_id==user_id,Token.is_active==True).all()
    if is_logged_in:
        raise HTTPException(status_code=409,detail="User already logged in.")
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

