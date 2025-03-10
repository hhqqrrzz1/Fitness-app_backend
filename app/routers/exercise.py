from app.models import Set, Exercise
from app.schemas import CreateSet, CreateExercise
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from app.backend.db_depends import get_db
from sqlalchemy import select, insert
from typing import Annotated

router = APIRouter(prefix='/exercises', tags=['exercises'])

# @router.put()