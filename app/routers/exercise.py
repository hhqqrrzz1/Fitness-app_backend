from app.models import Set, Exercise
from app.schemas import CreateSet, CreateExercise
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from app.backend.db_depends import get_db
from sqlalchemy import select, insert
from typing import Annotated

router = APIRouter(prefix='/exercises', tags=['exercises'])





#Логика CRUD для Set

@router.post('/{exercise_id}/sets/')
async def create_set(db: Annotated[AsyncSession, Depends(get_db)], create_set: CreateSet, exercise_id: int):
    exercise = await db.scalar(select(Exercise).where(Exercise.id == exercise_id))
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Exercise not found'
        )
    await db.execute(insert(Set).values(
        weight_rep_exe=create_set.weight_per_exe,
        reps=create_set.reps,
        exercise_id=exercise_id
    ))
    await db.commit()
    return {
        "status_code": status.HTTP_201_CREATED,
        "transaction": "successful"
    }