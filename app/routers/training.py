from app.models import Training, Set, MuscleGroup, Exercise
from app.schemas.create_schemas import CreateTraining
from app.schemas.response_schemas import TrainingResponse, TrainingResponsePatch
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from datetime import date
from app.routers.dependencies import db_session, current_user
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix='/trainings', tags=['trainings'])


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_training(db: db_session, create_training_data: CreateTraining, get_user: current_user):
    try:
        async with db.begin():
            user_id = get_user.get('id')
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
                    group_name=muscle_group_data.group_name.title(),
                    user_id=user_id
                )
                db.add(new_muscle_group)
                await db.flush()

                muscle_group_names.append(new_muscle_group.group_name)

                for exercise_data in muscle_group_data.exercises:
                    new_exercise = Exercise(
                        muscle_group_id=new_muscle_group.id,
                        exercise_name=exercise_data.exercise_name,
                        weight=exercise_data.weight,
                        numbers_reps=1,
                        user_id=user_id
                    )
                    db.add(new_exercise)
                    await db.flush()
                    cnt = 0

                    for set_data in exercise_data.sets:
                        new_set = Set(
                            exercise_id=new_exercise.id,
                            weight_per_exe=set_data.weight_per_exe,
                            reps=set_data.reps,
                            user_id=user_id
                        )
                        db.add(new_set)
                        cnt += 1
                    new_exercise.numbers_reps = cnt
            
            formatted_date = new_training.date.strftime("%d.%m.%Y")
            title = f"{formatted_date}-" + ', '.join(muscle_group_names)
            new_training.title = title
            db.add(new_training)

            return {
                    'status': status.HTTP_201_CREATED,
                    'transaction': 'New training created'
                }
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create training: {str(e)}"
        )


@router.get('/{training_id}', response_model=TrainingResponse)
async def get_training(db: db_session, training_id: int, get_user: current_user):
    training = await db.scalar(select(Training)
                               .options(
                                   selectinload(Training.muscle_groups).options(
                                       selectinload(MuscleGroup.exercises).options(
                                           selectinload(Exercise.sets)
                                       )
                                   )
                               )
                               .where(Training.id == training_id)
                            )
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Training not found'
        )
    if get_user.get('is_admin') or get_user.get('user_id') == training.user_id:
        return training
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )


@router.get("/all_workouts/", status_code=status.HTTP_200_OK)
async def get_number_of_trainings(db: db_session, get_user: current_user):
    """
    Функция, которая возвращает кол-во тренировок у юзера и выводит список всех его тренировок, в порядке возрастания даты
    """    
    user_id = get_user.get('id')
    all_trainings = await db.scalars(select(Training.title).where(Training.user_id == user_id).order_by(Training.date))
    title_list = all_trainings.all()
    if len(title_list) == 0:
        return {'message': 'You have no training'}

    return {
        "number_of_trainings": len(title_list),
        "trainings": title_list
    }


@router.patch("/update-training-date", response_model=TrainingResponsePatch)
async def update_training_date(db: db_session, get_user: current_user, training_id: int, update_date: date):
    try:
        async with db.begin():
            training = await db.scalar(select(Training)
                                       .options(selectinload(Training.muscle_groups))
                                       .where(Training.id == training_id))
            if not training:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тренировка не найдена")
            
            if get_user.get('is_admin') or get_user.get('id') == training.user_id:            
                if training.date == update_date:
                    return training
                
                muscle_group_names = [group.group_name.strip().title() for group in training.muscle_groups]
                formatted_date = update_date.strftime("%d.%m.%Y")
                new_title = f"{formatted_date}-" + ', '.join(muscle_group_names)
                
                training.date = update_date
                training.title = new_title
                db.add(training)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to patch training: {str(e)}"
        )
    return training


@router.delete('/{training_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_training(db: db_session, get_user: current_user, training_id: int):
    try:
        async with db.begin():
            training = await db.scalar(select(Training).where(Training.id == training_id))
            if not training:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Тренировка не найдена"
                )
            if get_user.get('is_admin') or get_user.get('id') == training.user_id:
                await db.execute(delete(Training).where(Training.id == training_id))
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )
                
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete exercise: {str(e)}"
        )
    return None