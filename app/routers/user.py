from fastapi import APIRouter, Depends, HTTPException, status
from app.models.users import User
from app.schemas import CreateUser
from app.backend.db_depends import get_db

from sqlalchemy import insert, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

router = APIRouter(prefix='/user', tags=['user'])

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


