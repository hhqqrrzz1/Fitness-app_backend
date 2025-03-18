from fastapi import HTTPException, APIRouter, status
from app.models.users import MuscleGroup, Training, Exercise, Set
from app.schemas.create_schemas import CreateMuscleGroup
from app.schemas.response_schemas import MuscleGroupResponse, MuscleGroupResponsePatch
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from app.routers.dependencies import db_session, current_user
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix='/muscle-groups', tags=['muscle-groups'])


@router.post('/')
async def create_muscle_group(
    db: db_session,
    create_data: CreateMuscleGroup,
    training_id: int
):
    try:
        async with db.begin():
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
                    detail="Muscle group with this name already exists for the training"
                )
            user_id = training.user_id

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
        return {
        'status': status.HTTP_201_CREATED,
        'transaction': 'successful'
    }
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create muscle group: {str(e)}"
        )


@router.get('/{muscle_group_id}', response_model=MuscleGroupResponse)
async def get_muscle_group(db: db_session, muscle_group_id: int, get_user: current_user):
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Muslce gtoup not found")
    if get_user.get('is_admin') or get_user.get('user_id') == muscle_group.user_id:
        return muscle_group
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )

@router.delete('/{muscle_group_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_muscle_group(
    db: db_session,
    muscle_group_id: int
):
    try:
        async with db.begin():
            muscle_group = await db.scalar(select(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
            if not muscle_group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Muscle group not found"
                )
            training = await db.scalar(select(Training).where(Training.id == muscle_group.training_id))
            group_names = [name.strip() for name in training.title.split("-")[1].split(",") if name.strip()]
            if len(group_names) == 1:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Can't remove the last muscle group"
                )
            group_names.remove(muscle_group.group_name.strip())

            new_title = f"{training.date.strftime('%d.%m.%Y')}-" + ", ".join(group_names)
            training.title = new_title
            db.add(training)

            result = await db.execute(delete(MuscleGroup).where(MuscleGroup.id == muscle_group_id))

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete muscle group: {str(e)}"
        )
    return None


@router.patch('/{muscle_group_id}', response_model=MuscleGroupResponsePatch)
async def rename_muscle_group(db: db_session, muscle_group_id: int, new_name: str):
    try:
        async with db.begin():
            updated_muscle_group = await db.scalar(select(MuscleGroup).where(MuscleGroup.id == muscle_group_id))
            if not updated_muscle_group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Muscle group not found'
                )
            old_name = updated_muscle_group.group_name.strip().title()
            if old_name.lower() == new_name.strip().lower():
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
            db.add(updated_muscle_group)
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to patch muscle group: {str(e)}"
        )
    return updated_muscle_group