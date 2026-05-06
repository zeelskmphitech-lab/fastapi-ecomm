from fastapi import FastAPI,Depends,HTTPException
from db.database import session,engine
import models.database_models as database_models
from schemas.models import User
from models.database_models import Users
from sqlalchemy.orm import Session
from sqlalchemy import text
from core.utils import get_hashed_password,verify_password,create_access_token,create_refresh_token

api = FastAPI()

database_models.base.metadata.create_all(bind=engine)

def get_db():
    db=session()
    try:
        yield db
    finally:
        db.close()
    
@api.get("/users/")
def get_users(db:Session= Depends(get_db)):
    return db.query(Users).all()

@api.post("/register/",status_code=201)
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
        return {"message":"User Created Successfully."}
    