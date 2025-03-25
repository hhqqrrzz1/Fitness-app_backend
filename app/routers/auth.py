from fastapi import APIRouter, Depends, HTTPException, status
from app.backend.db_depends import get_db
from app.models.all_models import User
from app.schemas.create_schemas import CreateUser
from sqlalchemy import insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from app.config import settings
from datetime import datetime, timedelta
from jose import jwt, JWTError

secret_key = settings.SECRET_KEY
algorithm = settings.ALGORITHM
full_rights = settings.full_rights_users

router = APIRouter(prefix='/auth', tags=['auth'])

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def create_access_token(username: str, user_id: int, is_admin: bool, is_guest: bool, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "is_admin": is_admin, "is_guest": is_guest}
    expires = datetime.now() + expires_delta
    encode.update({'exp': expires})
    
    return jwt.encode(encode, secret_key, algorithm=algorithm)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, secret_key, algorithms=algorithm)
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        is_admin: str = payload.get('is_admin')
        is_guest: str = payload.get('is_guest')
        expire = payload.get('exp')
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Could not validate user'
            )
        if expire is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='No access token supplied'
            )
        if datetime.now() > datetime.fromtimestamp(expire):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Token expired!'
            )
        return {
            'username': username,
            'id': user_id,
            'is_admin': is_admin,
            'is_guest': is_guest
        }
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )


async def authantificate_user(db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str):
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not bcrypt_context.verify(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentification creditionals",
            headers={"WWW-Authentificate": "Bearer"}
        )
    return user


@router.post("/token")
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await authantificate_user(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user"
        )
    token = await create_access_token(user.username, user.id, user.is_admin, user.is_guest, expires_delta=timedelta(minutes=20))
    
    return {
        'access_token': token,
        'token_type': 'bearer'
    }


@router.post('/')
async def create_user(db: Annotated[AsyncSession, Depends(get_db)], create_user: CreateUser):
    user = await db.scalar(select(User).where(or_(User.username == create_user.username, User.email == create_user.email)))
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Такой user уже существует")
    
    await db.execute(insert(User).values(
        username=create_user.username,
        password=bcrypt_context.hash(create_user.password),
        email=create_user.email
    ))
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        "transaction": "succsessful"
    }


@router.get('read_current_user')
async def read_current_user(user: Annotated[User, Depends(get_current_user)]):
    return {'User': user}