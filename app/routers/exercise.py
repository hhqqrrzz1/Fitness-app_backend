from app.models import Set, Exercise, MuscleGroup
from app.schemas.create_schemas import CreateExercise
from app.schemas.response_schemas import ExerciseResponse
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.routers.dependencies import current_user, db_session
from sqlalchemy.orm import selectinload
from logging_config import logger

router = APIRouter(prefix='/exercises', tags=['exercises'])


@router.post('/', response_model=ExerciseResponse)
async def create_exercise(
    db: db_session,
    get_user: current_user,
    create_data: CreateExercise,
    muscle_group_id: int
):
    try:
        logger.info(f"Попытка создать упражнение для гр. мышц с ID {muscle_group_id} пользователем {get_user.get('id')}")

        async with db.begin():
            muscle_group = await db.scalar(select(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
            if not muscle_group:
                logger.error(f"Мышечная гр. с ID {muscle_group_id} не найдена")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Muscle group not found"
                )
            
            user_id = muscle_group.user_id
            
            if get_user.get('is_admin') or get_user.get('id') == user_id:
                new_exercise = Exercise(
                    muscle_group_id=muscle_group_id,
                    exercise_name=create_data.exercise_name,
                    weight=create_data.weight,
                    numbers_reps=1,
                    user_id=user_id
                )
                db.add(new_exercise)
                await db.flush()    

                cnt = 0
                for set_data in create_data.sets:
                    new_set = Set(
                        exercise_id=new_exercise.id,
                        weight_per_exe=set_data.weight_per_exe,
                        reps=set_data.reps,
                        user_id=user_id
                    )
                    db.add(new_set)
                    cnt += 1

                new_exercise.numbers_reps = cnt

                logger.success(f"Упражнение успешно создано для гр. мышц с ID {muscle_group_id}")
                return {
                    'status': status.HTTP_201_CREATED,
                    'transaction': 'successful'
                }
            else:
                logger.warning(f"Пользователь {get_user.get('id')} не имеет необходимых прав для выполнения метода")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )
            
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Произошла ошибка целостности: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create exercise: {str(e)}"
        )


@router.get('/{exercise_id}', response_model=ExerciseResponse)
async def get_exercise(
    db: db_session,
    exercise_id: int,
    get_user: current_user
):
    try:
        logger.info(f"Попытка получения упражнения с ID {exercise_id} для пользователя {get_user.get('id')}")

        exercise = await db.scalar(
            select(Exercise)
            .options(selectinload(Exercise.sets))
            .where(Exercise.id == exercise_id)
        )
        if not exercise:
            logger.warning(f"Упражнение с ID {exercise_id} не найдено")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found"
            )
        
        if get_user.get('is_admin') or get_user.get('user_id') == exercise.user_id:
            logger.info(f"Пользователь с ID {get_user.get('id')} успешно получил упражнение с ID {exercise_id}")
            return exercise
        else:
            logger.warning(f"Пользователь {get_user.get('id')} не имеет необходимых прав для получения упражнения с ID {exercise_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='You are not authorized to use this method'
            )
    except HTTPException as e:
        logger.error(f"HTTP error occurred while fetching exercise {exercise_id}: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while fetching exercise {exercise_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )





@router.patch('/{exercise_id}', status_code=status.HTTP_200_OK, response_model=ExerciseResponse)
async def update_exercise(db: db_session, get_user: current_user, exercise_id: int, new_weight: float):
    try:
        logger.info(f"Attempted to patch exercise with ID {exercise_id} for user {get_user.get('id')}")
        async with db.begin():
            if new_weight < 0:
                logger.warning(f"User {get_user.get('id')} attempted to set negative weight ({new_weight}) for exercise {exercise_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail='New weight must be ge 0'
                )
            
            exercise = await db.scalar(select(Exercise).options(selectinload(Exercise.sets)).where(Exercise.id == exercise_id))

            if not exercise:
                logger.warning(f"User {get_user.get('id')} attempted to update non-existent exercise with ID {exercise_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="exercise not found"
                )
            if get_user.get('is_admin') or get_user.get('id') == exercise.user_id:
                if exercise.weight == new_weight:
                    logger.info(f"User {get_user.get('id')} attempted to update exercise {exercise_id}, but weight remains unchanged ({exercise.weight})")
                    return exercise
                
                exercise.weight = new_weight
                db.add(exercise)
                await db.flush()
            else:
                logger.warning(f"User {get_user.get('id')} attempted unauthorized access to exercise {exercise_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )
            logger.info(f"Weight for exercise ID {exercise_id} updated successfully from to {new_weight}")
            return exercise

    except IntegrityError as e:
            await db.rollback()
            logger.error(f"Database integrity error while updating exercise ID {exercise_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to patch exercise: {str(e)}"
            )
    except Exception as e:
        logger.error(f"Unexpected error while updating exercise ID {exercise_id} for user {get_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )


@router.delete('/{exercise_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(db: db_session, get_user: current_user, exercise_id: int):
    try:
        async with db.begin():
            logger.info(f"Пользователь {get_user.get('id')} птыается удалить упражнение {exercise_id}")
            exercise = await db.scalar(select(Exercise).where(Exercise.id == exercise_id))
            if not exercise:
                logger.warning(f"Упражнения с ID {exercise_id} нет")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Exercise not found'
                )
            if get_user.get('is_admin') or get_user.get('id') == exercise.user_id:
                muscle_group = await db.scalar(
                    select(MuscleGroup)
                    .options(selectinload(MuscleGroup.exercises))
                    .where(MuscleGroup.id == exercise.muscle_group_id)
                )
                if len(muscle_group.exercises) == 1:
                    logger.warning(f"Пользователь {get_user.geet('id')} пытается удалить последнее упражнение в тренировке {exercise_id}")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail='Can`t delete last exercise in muscle group'
                    )
                await db.execute(delete(Exercise).where(Exercise.id == exercise_id))
                logger.info(f"Упражнение с ID {exercise_id} успешно удалено")
                return None
            
            else:
                logger.warning(f"Пользователь {get_user.get('id')} не имеет необходимых прав для выполнения этого метода")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )
            
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Ошибка целостности БД: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete exercise: {str(e)}"
        )
