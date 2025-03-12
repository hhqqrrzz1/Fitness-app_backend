from app.models import Set, Exercise
from app.schemas import CreateSet, SetResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from app.backend.db_depends import get_db
from sqlalchemy import delete, select, insert, update

router = APIRouter(prefix='/sets', tags=['sets'])

@router.get('/{set_id}', response_model=SetResponse)
async def get_set(db: Annotated[AsyncSession, Depends(get_db)], set_id: int):
    set = await db.scalar(select(Set).where(Set.id == set_id))
    if not set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found"
        )
    return set

@router.get('/')
async def get_all_set_by_exercise(db: Annotated[AsyncSession, Depends(get_db)], exercise_id: int):
    exercise = await db.scalar(select(Exercise).where(Exercise.id == exercise_id))
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Exercise not found'
        )
    sets = await db.scalars(select(Set).where(Set.exercise_id == exercise_id))
    return sets.all()

@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_set(db: Annotated[AsyncSession, Depends(get_db)], create_set: CreateSet, exercise_id: int):
    exercise = await db.scalar(select(Exercise).where(Exercise.id == exercise_id))
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    new_set = Set(
        exercise_id=exercise_id,
        weight_per_exe=create_set.weight_per_exe,
        reps=create_set.reps
    )
    db.add(new_set)
    await db.flush()

    exercise.numbers_reps += 1
    db.add(exercise)

    await db.commit()

    return new_set

@router.delete('/{set_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_set(db: Annotated[AsyncSession, Depends(get_db)], set_id: int):
    set_to_delete = await db.scalar(select(Set).where(Set.id == set_id))
    if not set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Set not found'
        )
    
    exercise = await db.scalar(select(Exercise).where(Exercise.id == set_to_delete.exercise_id))

    if exercise.numbers_reps == 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can't delete last approach"
        )
    else:
        await db.execute(delete(Set).where(Set.id == set_id))
        exercise.numbers_reps -= 1
    
    db.add(exercise)
    await db.commit()

    return None

@router.put('/{set_id}', status_code=status.HTTP_200_OK, response_model=SetResponse)
async def update_set(db: Annotated[AsyncSession, Depends(get_db)], set_id: int, new_data: CreateSet):
    set_to_update = await db.scalar(select(Set).where(Set.id == set_id))
    if not set_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found"
        )
    
    if (
        set_to_update.weight_per_exe == new_data.weight_per_exe and
        set_to_update.reps == new_data.reps
    ):
        return set_to_update

    try:
        set_to_update.weight_per_exe = new_data.weight_per_exe
        set_to_update.reps = new_data.reps

        db.add(set_to_update)
        await db.commit()
        await db.refresh()

        return set_to_update
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update set: {str(e)}"
        )