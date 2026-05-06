from fastapi import FastAPI,Depends,HTTPException
from database import session,engine
import database_models
from models import User
from database_models import Users
from sqlalchemy.orm import Session
from sqlalchemy import text

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
    new_user = Users(**user.model_dump())
    
    if is_email_exists:
        raise HTTPException(status_code=409,detail="Email Already registered.")
    else:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    
@api.put("/users/{id}")
def update_user(id,user:User,db:Session=Depends(get_db)):
    is_user_exists = db.query(Users).filter(Users.id==id).first()
    if not is_user_exists:
        raise HTTPException(status_code=404,detail='User not found.')
    