from app.models import Set, Exercise
from app.schemas import CreateSet
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from app.backend.db_depends import get_db
from sqlalchemy import select, insert

router = APIRouter(tags=['sets'])

@router.post('/exercises/{exercise_id}/sets/')
async def create_set(db: Annotated[AsyncSession, Depends(get_db)], create_set: CreateSet, exercise_id: int):
    pass
