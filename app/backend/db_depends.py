from ..backend.db import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession

async def get_db() -> AsyncSession: # type: ignore
    async with async_session_maker() as session:
        yield session