from fastapi import APIRouter, Depends, HTTPException, status
from app.models.users import User, Training
from app.schemas.create_schemas import CreateUser
from app.backend.db_depends import get_db

from sqlalchemy import insert, or_, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from .env import SECRET_KEY, ALHGORITM

router = APIRouter(prefix='/auth', tags=['auth'])
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

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


async def authantificate_user(db: Annotated[AsyncSession, Depends(get_db)], username: str, password: str):
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not bcrypt_context.verify(password, user.password) or user.is_active == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentification creditionals",
            headers={"WWW-Authentificate": "Bearer"}
        )
    return user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

@router.post("/token")
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = await authantificate_user(db, form_data.username, form_data.password)

    if not user or user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user"
        )
    return {
        'access_token': user.username,
        'token_type': 'bearer'
    }

# @router.get('/{user_id}', status_code=status.HTTP_200_OK)
# async def get_user(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
#     user = await db.scalar(select(User).where(User.id == user_id))
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail='User not found'
#         )
#     return user



# @router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_user(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
#     user = await db.scalar(select(User).where(User.id == user_id))
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail='User not found'
#         )
#     await db.execute(delete(User).where(User.id == user_id))
#     await db.commit()
#     return None

@router.get("/all_workouts/{user_id}", status_code=status.HTTP_200_OK)
async def get_number_of_trainings(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
    """Функция, которая возвращает кол-во тренировок у юзера и выводит список всех его тренировок, в порядке возрастания даты"""
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    all_trainings = await db.scalars(select(Training.title).where(Training.user_id == user_id).order_by(Training.date))
    title_list = all_trainings.all()

    return {
        "number_of_trainings": len(title_list),
        "trainings": title_list
    }