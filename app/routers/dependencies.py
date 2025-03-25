from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from fastapi import HTTPException, status

from app.routers.auth import get_current_user
from app.backend.db_depends import get_db

db_session = Annotated[AsyncSession, Depends(get_db)]
current_user = Annotated[dict, Depends(get_current_user)]