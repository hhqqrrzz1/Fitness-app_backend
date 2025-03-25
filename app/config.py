from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    SECRET_KEY: str
    ALGORITHM: str
    FULL_RIGHTS: str

    def get_db_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def full_rights_users(self) -> list[str]:
        """Преобразует строку full_rights в список"""
        return self.FULL_RIGHTS.split(',')
    
    class Config:
        env_file = Path(__file__).parent / '.env'
        env_file_encoding = 'utf-8'

settings = Settings()
