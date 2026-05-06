from pydantic import BaseModel,EmailStr,Field
from typing import Annotated,Optional,Any

class User(BaseModel):
    first_name : str
    last_name : str
    username : str
    email : EmailStr
    # password : str
    
class UserInDB(User):
    hased_password : str