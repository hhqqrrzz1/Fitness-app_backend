from sqlalchemy import Column, String, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from ..backend import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)

    trainings = relationship("Training", back_populates="user")

class Training(Base):
    __tablename__ = 'trainings'

    id = Column(Integer, index=True, primary_key=True)
    date = Column(Date)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates='trainings')
