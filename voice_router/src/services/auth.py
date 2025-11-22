from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from typing import Optional
from core.config import settings
from http import HTTPStatus


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if credentials:
            token = credentials.credentials
            try:
                payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
                return payload  # Можно передать как user
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Token expired")
            except jwt.JWTError:
                raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Invalid token")
        raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Authorization required")
