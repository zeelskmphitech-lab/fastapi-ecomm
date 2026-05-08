import secrets
from passlib.context import CryptContext
from jose import jwt
from typing import Any
from datetime import datetime,timedelta,UTC

ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_MINUTES = 60*24*7
ALGORITHM = 'HS256'

# python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY = "I5epMhX-ziAGeOP4AnW8y4e6rU_hSVANYVB6KMACjvI"
JWT_REFRESH_SECRET_KEY = "PzToNqGHNeJaBUBQB0cdnL7LXraKKMAHA7wKzGG30nc"

password_context = CryptContext(schemes=['bcrypt'],deprecated = 'auto')

def get_hashed_password(password:str)->str:
    return password_context.hash(password)

def verify_password(password:str,hashed_password:str)->bool:
    return password_context.verify(password,hashed_password)

def create_access_token(subject: str | Any,expiry_time:int=None)->str:
    if expiry_time is not None:
        expiry_time = datetime.now(UTC)+expiry_time
    else:
        expiry_time = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {
        "exp": expiry_time,
        "sub": str(subject),
        "iat": datetime.now(UTC),
        "jti": secrets.token_urlsafe(16),
    }
    encode_jwt = jwt.encode(to_encode,JWT_SECRET_KEY,ALGORITHM)
    return encode_jwt

def create_refresh_token(subject: str | Any,expiry_time:int=None)->str:
    if expiry_time is not None:
        expiry_time =  datetime.now(UTC) + expiry_time
    else:
        expiry_time = datetime.now(UTC) + timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
        
    to_encode = {
        "exp": expiry_time,
        "sub": str(subject),
        "iat": datetime.now(UTC),
        "jti": secrets.token_urlsafe(16),
    }
    encode_jwt = jwt.encode(to_encode,JWT_REFRESH_SECRET_KEY,ALGORITHM)
    return encode_jwt