from jwt.exceptions import InvalidTokenError
from jose import jwt
from .utils import JWT_SECRET_KEY,ALGORITHM
from fastapi import HTTPException,Request
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer

def decode_jwt(jwtoken:str):
    try:
        payload = jwt.decode(jwtoken,JWT_SECRET_KEY,ALGORITHM)
        return payload
    except InvalidTokenError:
        return None
    
class JWTBearer(HTTPBearer):
    def __init__(self,auto_error:bool=True):
        super(JWTBearer,self).__init__(auto_error=auto_error)
        
    async def __call__(self,request:Request):
        credentials : HTTPAuthorizationCredentials = await super(JWTBearer,self,).__call__(request)
        
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=403,detail="Invalid Authentication Schema")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=403,detail="Invalid Token Or Expired.")
            return credentials.credentials
        else:
            raise HTTPException(status_code=403,detail="Invalid Authorization code.")
            
            
    def verify_jwt(self,jwtoken:str)->bool:
        isTokenValid: bool = False
        
        try:
            payload = decode_jwt(jwtoken)
        except:
            payload = None
            
        if payload:
            isTokenValid = True
            
        return isTokenValid