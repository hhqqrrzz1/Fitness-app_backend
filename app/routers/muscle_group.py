from fastapi import Depends, HTTPException, APIRouter, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db_depends import get_db
from app.models.users import MuscleGroup, Training, Exercise, Set
from app.schemas import CreateMuscleGroup, CreateExercise, CreateSet
from typing import Annotated
from sqlalchemy import select, delete, update
from datetime import date
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix='/muscle-groups', tags=['muscle-groups'])

@router.get('/{muscle_group_id}')
async def get_muscle_group(db: Annotated[AsyncSession, Depends(get_db)], muscle_group_id: int):
    muscle_group = await db.scalar(select(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
    if not muscle_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Muslce gtoup not found")
    return muscle_group

@router.delete('/{muscle_group_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_muscle_group(
    db: Annotated[AsyncSession, Depends(get_db)],
    muscle_group_id: int
):
    muscle_group = await db.scalar(select(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
    if not muscle_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Muscle group not found"
        )
    training = await db.scalar(select(Training).where(Training.id == muscle_group.training_id))
    group_names = [name.strip() for name in training.title.split("-")[1].split(",") if name.strip()]
    group_names.remove(muscle_group.group_name.strip())
    if group_names:
        new_title = f"{training.date.strftime('%d.%m.%Y')}-" + ", ".join(group_names)
    else:
        new_title = training.date.strftime('%d.%m.%Y')

    training.title = new_title
    db.add(training)

    result = await db.execute(delete(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete muscle group"
        )
    await db.commit()
    return None

@router.post('/')
async def create_muscle_group(
    db: Annotated[AsyncSession, Depends(get_db)],
    create_data: CreateMuscleGroup,
    training_id: int
):
    training = await db.scalar(select(Training).where(Training.id == training_id))
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training not found"
        )
    #Проверим наличие данной гр. мышц в тренировке
    exesting_group = await db.scalar(
        select(MuscleGroup).where(
            MuscleGroup.training_id == training_id,
            MuscleGroup.group_name == create_data.group_name.title()
        )
    )
    if exesting_group:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Muscle group with this name in training"
        )

    new_muscle_group = MuscleGroup(
        training_id=training_id,
        group_name=create_data.group_name.title()
    )
    db.add(new_muscle_group)
    await db.flush()

    new_title = training.title + f", {new_muscle_group.group_name}"
    training.title = new_title
    db.add(training)

    try:
        for exercise_data in create_data.exercises:
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
        return new_muscle_group
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create muscle group: {str(e)}"
        )
    
