from app.models import Set, Exercise, MuscleGroup
from app.schemas import CreateSet, CreateExercise, ExerciseResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, Body
from app.backend.db_depends import get_db
from sqlalchemy import select, insert, update
from typing import Annotated
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload

router = APIRouter(prefix='/exercises', tags=['exercises'])

@router.get('/{exercise_id}', response_model=ExerciseResponse)
async def get_exercise(
    db:Annotated[AsyncSession, Depends(get_db)],
    exercise_id: int
):
    exercise = await db.scalar(
        select(Exercise)
        .options(selectinload(Exercise.sets))
        .where(Exercise.id == exercise_id)
    )
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Exercise not found"
        )
    return exercise

@router.post('/')
async def create_exercise(
    db:Annotated[AsyncSession, Depends(get_db)],
    create_data: CreateExercise,
    muscle_group_id: int
):
    muscle_group = await db.scalar(select(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
    if not muscle_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Muscle group not found"
        )
    #Проверим наличие данного упр.
    exesting_exercise = await db.scalar(
        select(Exercise).where(
            Exercise.muscle_group_id == muscle_group_id,
            Exercise.exercise_name == create_data.exercise_name
        )
    )
    if exesting_exercise:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail='Exercise with this name alredy exists for the muscle_group '
        )
    
    new_exercise = Exercise(
        muscle_group_id=muscle_group_id,
        exercise_name=create_data.exercise_name,
        weight=create_data.weight,
        numbers_reps=1
    )
    db.add(new_exercise)
    await db.flush()
    cnt = 0

    try:
        for set_data in create_data.sets:
            new_set = Set(
                exercise_id=new_exercise.id,
                weight_per_exe=set_data.weight_per_exe,
                reps=set_data.reps
            )
            db.add(new_set)
            cnt += 1
        new_exercise.numbers_reps = cnt
        
        await db.commit()
        return new_exercise
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create exercise: {str(e)}"
        )

@router.patch('/{exercise_id}', status_code=status.HTTP_200_OK)
async def update_exercise(db: Annotated[AsyncSession, Depends(get_db)], exercise_id: int, new_weight: Annotated[int, Body(ge=0)]):
    exercise = await db.scalar(select(Exercise).where(Exercise.id == exercise_id))
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="exercise not found"
        )
    await db.execute(update(Exercise).where(Exercise.id == exercise_id).values(weight = new_weight))
    await db.commit()

    updated_exercise = await db.scalar(select(Exercise).where(Exercise.id == exercise_id))
    return updated_exercise