from fastapi import APIRouter, Depends, HTTPException, status
from app.models.users import User, Training
from app.schemas import CreateUser
from app.backend.db_depends import get_db

from sqlalchemy import insert, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

router = APIRouter(prefix='/users', tags=['users'])

@router.post('/')
async def create_user(db: Annotated[AsyncSession, Depends(get_db)], create_user: CreateUser):
    user = await db.scalar(select(User).where(or_(User.username == create_user.username, User.email == create_user.email)))
    if user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Такой user уже существует")
    await db.execute(insert(User).values(
        username=create_user.username,
        password=create_user.password,
        email=create_user.email
    ))
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        "transaction": "succsessful"
    }


@router.get('/{user_id}', status_code=status.HTTP_200_OK)
async def get_user(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    return user



@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found'
        )
    await db.execute(update(User).where(User.id == user_id).values(is_active = False))
    await db.commit()
    return None

@router.get("/all_workouts/{user_id}", status_code=status.HTTP_200_OK)
async def get_number_of_trainings(db: Annotated[AsyncSession, Depends(get_db)], user_id: int):
    user = await db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    all_trainings = await db.scalars(select(Training.title).where(Training.user_id == user_id))
    title_list = all_trainings.all()

    return {
        "number_of_trainings": len(title_list),
        "trainings": title_list
    }