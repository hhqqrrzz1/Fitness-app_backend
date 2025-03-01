from app.models import Training, Set, MuscleGroup, Exercise
from app.schemas import CreateExercise, CreateMuscleGroup, CreateSet, CreateTraining
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from app.backend.db_depends import get_db
from sqlalchemy import select, insert

router = APIRouter(prefix='/trainings', tags=['trainings'])

@router.get('/{training_id}')
async def get_training(db: Annotated[AsyncSession, Depends(get_db)], training_id: int):
    training = await db.scalar(select(Training).where(Training.id == training_id))
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Training not found'
        )
    return training

@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_training(db: Annotated[AsyncSession, Depends(get_db)], create_training_data: CreateTraining, user_id: int):
    new_training = Training(
        date=create_training_data.date,
        user_id=user_id
    )
    db.add(new_training)
    await db.flush()

    for muscle_group_data in create_training_data.muscle_groups:
        new_muscle_group = MuscleGroup(
            training_id=new_training.id,
            group_name=muscle_group_data.group_name
        )
        db.add(new_muscle_group)
        await db.flush()

        for exercise_data in muscle_group_data.exercises:
            new_exercise = Exercise(
                muscle_group_id=new_muscle_group.id,
                exercise_name=exercise_data.exercise_name,
                weight=exercise_data.weight,
                numbers_reps=exercise_data.numbers_reps
            )
            db.add(new_exercise)
            await db.flush()

            for set_data in exercise_data.sets:
                new_set = Set(
                    exercise_id=new_exercise.id,
                    weight_per_exe=set_data.weight_per_exe,
                    reps=set_data.reps
                )
                db.add(new_set)
    await db.commit()
    return new_training