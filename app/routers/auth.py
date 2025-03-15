from fastapi import APIRouter, Depends, HTTPException, status
from app.models.users import User
from app.schemas.create_schemas import CreateUser
from app.backend.db_depends import get_db
from sqlalchemy import insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from .env import SECRET_KEY, ALHGORITM
from datetime import datetime, timedelta
from jose import jwt, JWTError


router = APIRouter(prefix='/auth', tags=['auth'])

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def create_access_token(username: str, user_id: int, is_admin: bool, is_guest: bool, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "is_admin": is_admin, "is_guest": is_guest}
    expires = datetime.now() + expires_delta
    encode.update({'exp': expires})
    
    return jwt.encode(encode, SECRET_KEY, algorithm=ALHGORITM)


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALHGORITM)
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



# @router.get("/all_workouts/{user_id}", status_code=status.HTTP_200_OK)
# async def get_number_of_trainings(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
#     """Функция, которая возвращает кол-во тренировок у юзера и выводит список всех его тренировок, в порядке возрастания даты"""
#     user = await db.scalar(select(User).where(User.id == user_id))
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
#     all_trainings = await db.scalars(select(Training.title).where(Training.user_id == user_id).order_by(Training.date))
#     title_list = all_trainings.all()

#     return {
#         "number_of_trainings": len(title_list),
#         "trainings": title_list
#     }