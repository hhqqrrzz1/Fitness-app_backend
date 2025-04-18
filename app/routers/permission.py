from fastapi import APIRouter, status, HTTPException
from sqlalchemy import select, update, delete
from app.models.all_models import User
from app.config import settings
from app.routers.dependencies import current_user, db_session
from logging_config import logger

router = APIRouter(prefix='/permission', tags=['permission'])
full_rights = settings.full_rights_users

@router.patch('/')
async def admin_permission(
    db: db_session,
    get_user: current_user,
    user_id: int
):
    if get_user.get('is_admin') and get_user.get('username') in full_rights:
        user = await db.scalar(select(User).where(User.id == user_id))

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        if user.username in full_rights:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='This user has protected rights and cannot be modified'
            )
        if user.is_admin:
            await db.execute(update(User).where(User.id == user_id).values(is_admin=False, is_guest=True))
            await db.commit()
            logger.info(f"Больше пользователь с ID {user_id} не admin")
            return {
                'status': status.HTTP_200_OK,
                'detail': "User is no longer admin"
            }
        else:
            await db.execute(update(User).where(User.id == user_id).values(is_admin=True, is_guest=False))
            await db.commit()
            logger.info(f"Теперь пользователь с ID {user_id} admin")
            return {
                'status': status.HTTP_200_OK,
                'detail': 'User is now admin'
            }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You don`t have admin permission'
        )
    
@router.delete('/delete', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: db_session,
    get_user: current_user,
    user_id: int
):
    if get_user.get('is_admin'):
        user = await db.scalar(select(User).where(User.id == user_id))
    
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='User not found'
            )
        if user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='You can`t delete admin user'
            )
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        return None
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You don`t have admin permission'
        )

@router.get('/get_id')
async def get_user_id(db: db_session, get_user: current_user, username: str):
    if get_user.get("is_admin"):
        user_id = await db.scalar(select(User.id).where(User.username == username))
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return {
            'status': status.HTTP_200_OK,
            'user_id': user_id
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You don`t have admin permission'
        )
    