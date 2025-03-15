from app.models import Training, Set, MuscleGroup, Exercise
from app.schemas.create_schemas import CreateTraining
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from app.backend.db_depends import get_db
from sqlalchemy import select, delete, update
from datetime import date

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

    muscle_group_names = []

    for muscle_group_data in create_training_data.muscle_groups:
        new_muscle_group = MuscleGroup(
            training_id=new_training.id,
            group_name=muscle_group_data.group_name.title()
        )
        db.add(new_muscle_group)
        await db.flush()

        muscle_group_names.append(new_muscle_group.group_name)

        for exercise_data in muscle_group_data.exercises:
            new_exercise = Exercise(
                muscle_group_id=new_muscle_group.id,
                exercise_name=exercise_data.exercise_name,
                weight=exercise_data.weight,
                numbers_reps=1
            )
            db.add(new_exercise)
            await db.flush()
            cnt = 0

            for set_data in exercise_data.sets:
                new_set = Set(
                    exercise_id=new_exercise.id,
                    weight_per_exe=set_data.weight_per_exe,
                    reps=set_data.reps
                )
                db.add(new_set)
                cnt += 1
            new_exercise.sets = cnt
    
    formatted_date = new_training.date.strftime("%d.%m.%Y")
    title = f"{formatted_date}-" + ', '.join(muscle_group_names)
    new_training.title = title
    db.add(new_training)

    await db.commit()
    return new_training

@router.patch("/update-training-date")
async def update_training_date(db: Annotated[AsyncSession, Depends(get_db)], update_date: date, training_id: int):
    training = await db.scalar(select(Training).where(Training.id == training_id))
    
    if not training:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тренировка не найдена")
    
    muscle_group_names = await db.scalars(select(MuscleGroup.group_name).where(MuscleGroup.training_id == training_id))
    formatted_date = update_date.strftime("%d.%m.%Y")
    new_title = f"{formatted_date}-" + ', '.join(muscle_group_names.all())
    
    await db.execute(update(Training).where(Training.id == training_id).values(date=update_date, title=new_title))
    await db.commit()
    return {
        "status_code": status.HTTP_200_OK,
        "transaction": "Training update is successful"
    }

@router.delete('/{training_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_training(db: Annotated[AsyncSession, Depends(get_db)], training_id: int):
    training = await db.scalar(select(Training).where(Training.id == training_id))
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тренировка не найдена"
        )
    await db.execute(delete(Training).where(Training.id == training_id))
    await db.commit()

    return None