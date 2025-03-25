from typing import List
from app.models import Set, Exercise
from app.schemas.create_schemas import CreateSet
from app.schemas.response_schemas import SetResponse
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select
from app.routers.dependencies import db_session, current_user
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix='/sets', tags=['sets'])


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_set(db: db_session, get_user: current_user, create_set: CreateSet, exercise_id: int):
    try:
        async with db.begin():
            exercise = await db.scalar(select(Exercise).where(Exercise.id == exercise_id))
            if not exercise:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Exercise not found"
                )
            if get_user.get('is_admin') or get_user.get('id') == exercise.user_id:
                new_set = Set(
                    exercise_id=exercise_id,
                    weight_per_exe=create_set.weight_per_exe,
                    reps=create_set.reps,
                    user_id=exercise.user_id
                )
                db.add(new_set)
                await db.flush()

                exercise.numbers_reps += 1
                db.add(exercise)
                return {
            'status': status.HTTP_201_CREATED,
            'transaction': 'New set created'
        }
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create set: {str(e)}"
        )


@router.get('/{set_id}', response_model=SetResponse)
async def get_set(db: db_session, set_id: int, get_user: current_user):
    set = await db.scalar(select(Set).where(Set.id == set_id))
    if not set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found"
        )
    if get_user.get('is_admin') or get_user.get('user_id') == set.user_id:
        return set
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )


@router.get('/', response_model=List[SetResponse])
async def get_all_set_by_exercise(db: db_session, exercise_id: int, get_user: current_user):
    exercise = await db.scalar(select(Exercise).where(Exercise.id == exercise_id))
    if not exercise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Exercise not found'
        )
    if get_user.get('is_admin') or get_user.get('user_id') == exercise.user_id:
        sets = await db.scalars(select(Set).where(Set.exercise_id == exercise_id))
        return sets.all()
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )


@router.delete('/{set_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_set(db: db_session, get_user: current_user, set_id: int):
    try:
        async with db.begin():
            set_to_delete = await db.scalar(select(Set).where(Set.id == set_id))
            if not set:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail='Set not found'
                )
            if get_user.get('is_admin') or get_user.get('id') == set_to_delete.user_id:
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
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )

    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete set: {str(e)}"
        )
    return None


@router.put('/{set_id}', status_code=status.HTTP_200_OK, response_model=SetResponse)
async def update_set(db: db_session, get_user: current_user, set_id: int, new_data: CreateSet):
    try:
        async with db.begin():
            set_to_update = await db.scalar(select(Set).where(Set.id == set_id))
            if not set_to_update:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Set not found"
                )
            if get_user.get('is_admin') or get_user.get('id') == set_to_update.user_id:
                if (
                    set_to_update.weight_per_exe == new_data.weight_per_exe and
                    set_to_update.reps == new_data.reps
                ):
                    return set_to_update

                set_to_update.weight_per_exe = new_data.weight_per_exe
                set_to_update.reps = new_data.reps
                db.add(set_to_update)
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='You are not authorized to use this method'
                )
  
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update set: {str(e)}"
        )
    await db.refresh(set_to_update)
    return set_to_update