from fastapi import FastAPI,Depends,HTTPException
from db.database import session,engine
import models.database_models as database_models
from schemas.models import User,TokenCreate,RequestDetail,UserResponse,TokenResponse
from models.database_models import Users,Token
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.utils import get_hashed_password,verify_password,create_access_token,create_refresh_token
from core.auth_bearer import JWTBearer

api = FastAPI()

database_models.base.metadata.create_all(bind=engine)

def get_db():
    db=session()
    try:
        yield db
    finally:
        db.close()
    
@api.get("/users/")
def get_users(dependencies=Depends(JWTBearer),db:Session= Depends(get_db)):
    user = db.query(Users).all()
    return user

@api.post("/register/",status_code=201,response_model=UserResponse)
def add_user(user:User,db:Session=Depends(get_db)):
    is_email_exists =db.query(Users).filter(Users.email==user.email).first()
    hashed_password = get_hashed_password(user.password)
    new_user = Users(first_name=user.first_name,last_name=user.last_name,username=user.username,email=user.email,password=hashed_password)
    
    if is_email_exists:
        raise HTTPException(status_code=409,detail="Email Already registered.")
    else:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
@api.post('/login/',response_model=TokenResponse)
def user_login(request : RequestDetail,db:Session=Depends(get_db)):
    user = db.query(Users).filter(Users.email==request.email).first()
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
    return {"access_token":access_token,"refresh_token":refresh_token}