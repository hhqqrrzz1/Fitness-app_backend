from fastapi import HTTPException, APIRouter, status
from app.models.all_models import MuscleGroup, Training, Exercise, Set
from app.schemas.create_schemas import CreateMuscleGroup
from app.schemas.response_schemas import MuscleGroupResponse, MuscleGroupResponsePatch
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.routers.dependencies import db_session, current_user
from sqlalchemy.exc import IntegrityError
from logging_config import logger

router = APIRouter(prefix='/muscle-groups', tags=['muscle-groups'])


@router.post('/')
async def create_muscle_group(
    db: db_session,
    get_user: current_user,
    create_data: CreateMuscleGroup,
    training_id: int
):
    try:
        async with db.begin():
            logger.info(f"Пользователь {get_user.get('id')} пытается создать новую мыш. группу")
            training = await db.scalar(select(Training).where(Training.id == training_id))
            if not training:
                logger.warning(f"Пользователь {get_user.get('id')} пытается создать новую группу мышц в несуществующей тренировке")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Training not found"
                )

            user_id = training.user_id

            if get_user.get('is_admin') or get_user.get('id') == user_id:
                new_muscle_group = MuscleGroup(
                    training_id=training_id,
                    group_name=create_data.group_name.title(),
                    user_id=user_id
                )
                db.add(new_muscle_group)
                await db.flush()

                new_title = training.title + f", {new_muscle_group.group_name}"
                training.title = new_title
                db.add(training)

                for exercise_data in create_data.exercises:
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

            else:
                logger.warning(f"Пользователь {get_user.get('id')} не имеет необходимых прав для выполнения этого метода")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )
            logger.info(f"Пользователь {get_user.get('id')} успешно создал мышечную группу '{new_muscle_group.group_name}' с ID {new_muscle_group.id}")
            return {
            'status': status.HTTP_201_CREATED,
            'transaction': 'successful'
        }
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Ошибка целостности БД для создания гр. мышц для пользователя {get_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to patch exercise: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Неожиданная ошибка при создании гр. мышц для пользователя {get_user.get('id')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error"
        )

@router.get('/{muscle_group_id}', response_model=MuscleGroupResponse)
async def get_muscle_group(db: db_session, muscle_group_id: int, get_user: current_user):
    logger.info(f"Пользователь {get_user.get('id')} пытается получить гр. мышц с ID {muscle_group_id}")
    muscle_group = await db.scalar(
        select(MuscleGroup)
        .options(
            selectinload(MuscleGroup.exercises).options(
                selectinload(Exercise.sets)
            )
        )
        .where(MuscleGroup.id == muscle_group_id)
    )

    if not muscle_group:
        logger.warning(f"Гр. мышц {muscle_group_id} нет")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Muslce gtoup not found")

    if get_user.get('is_admin') or get_user.get('user_id') == muscle_group.user_id:
        logger.info(f"Пользователь {get_user.get('id')} успешно получил гр. мышц {muscle_group_id}")
        return muscle_group
    else:
        logger.warning(f"Пользователь {get_user.get('id')} не имеет необходимых правв для получения гр. мышц {muscle_group_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )

@router.delete('/{muscle_group_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_muscle_group(
    db: db_session,
    muscle_group_id: int,
    get_user: current_user
):
    try:
        async with db.begin():
            logger.info(f"Пользователь {get_user.get('id')} пытается удалить гр. мышц {muscle_group_id}")
            muscle_group = await db.scalar(select(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
            if not muscle_group:
                logger.warning(f"Гр. мышц с ID {muscle_group_id} нет")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Muscle group not found"
                )
            if get_user.get('is_admin') or get_user.get('id') == muscle_group.user_id:
                training = await db.scalar(select(Training).where(Training.id == muscle_group.training_id))
                group_names = [name.strip() for name in training.title.split("-")[1].split(",") if name.strip()]
                if len(group_names) == 1:
                    logger.info(f"Пользователь {get_user.get('id')} пытается удалить единственную гр. мышц в тренировке {training.id}")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Can't remove the last muscle group"
                    )
                
                group_names.remove(muscle_group.group_name.strip())

                new_title = f"{training.date.strftime('%d.%m.%Y')}-" + ", ".join(group_names)
                training.title = new_title
                logger.info(f"Название тренировки {training.id} успешно измененно на {new_title}")

                db.add(training)

                await db.execute(delete(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
                logger.info(f"Гр. мышц {muscle_group_id} успешно удалена")
                return None
            
            else:
                logger.warning(f"Пользователь {get_user.get('id')} не имеет необходимых прав для использования этого метода")
                raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Ошибка целостности БД: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete muscle group: {str(e)}"
        )


@router.patch('/{muscle_group_id}', response_model=MuscleGroupResponsePatch)
async def rename_muscle_group(db: db_session, get_user: current_user, muscle_group_id: int, new_name: str):
    try:
        async with db.begin():
            logger.info(f"Пользователь {get_user.get('if')} пытается изменить название для гр. мышц {muscle_group_id}")
            updated_muscle_group = await db.scalar(select(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
            if not updated_muscle_group:
                logger.warning(f"Гр. мышц с ID {muscle_group_id} нет")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Muscle group not found'
                )
            
            if get_user.get('is_admin') or get_user.get('id') == updated_muscle_group.user_id:
                old_name = updated_muscle_group.group_name.strip().title()
                if old_name.lower() == new_name.strip().lower():
                    logger.info(f"Пользователь {get_user.get('id')} ввел такое же название")
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail='Same names'
                    )
                
                updated_training = await db.scalar(select(Training).where(Training.id == updated_muscle_group.training_id))

                group_names = [name.strip(',') for name in updated_training.title.split('-')[1].split() if name.strip()]
                group_names = [name for name in group_names if name != old_name]
                group_names.append(new_name.strip().title())
                
                new_title = f"{updated_training.date.strftime('%d.%m.%Y')}-" + ", ".join(group_names)
                updated_training.title = new_title
                updated_muscle_group.group_name = new_name.strip().title()
                db.add(updated_training)
                logger.info(f"Название тренировки изменено с учетом нового названия для гр. мышц {muscle_group_id}")
                db.add(updated_muscle_group)
            else:
                logger.warning(f"Пользователь {get_user.get('id')} не имеет необходимых прав для данного метода")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )
            logger.info(f"Пользователь {get_user.get('id')} успешно изменил название для гр. мышц")
            return updated_muscle_group
        
    except IntegrityError as e:
        await db.rollback()
        logger.error(f"Ошибка целостности БД: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to patch muscle group: {str(e)}"
        )
