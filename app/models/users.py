from sqlalchemy import Column, String, Integer, ForeignKey, Date, Boolean
from sqlalchemy.orm import relationship, mapped_column, Mapped
from typing import List
from ..backend import Base

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    trainings: Mapped[List["Training"]] = relationship("Training", back_populates='user', cascade='all, delete-orphan')

class Training(Base):
    __tablename__ = 'trainings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] =  mapped_column(Date)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))

    user: Mapped["User"] = relationship("User", back_populates='trainings')
    muscle_groups: Mapped[List["MuscleGroup"]] = relationship("MuscleGroup", back_populates='training')


class MuscleGroup(Base):
    __tablename__ = "muscle_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    training_id: Mapped[int] = mapped_column(Integer, ForeignKey("trainings.id"))
    group_name: Mapped[str] = mapped_column(String, nullable=False)

    training: Mapped["Training"] = relationship("Training", back_populates='muscle_groups')
    exercices: Mapped[List["Exercise"]] = relationship("Exercise", back_populates="muscle_group")

class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    muscle_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("muscle_groups.id"))
    exercise_name: Mapped[str] = mapped_column(String, nullable=False)
    weight: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    numbers_reps: Mapped[int] = mapped_column(Integer, nullable=False)

    muscle_group: Mapped["MuscleGroup"] = relationship("MuscleGroup", back_populates='exercises')
    sets: Mapped[List["Set"]] = relationship("Set", back_populates='exercise')

class Set(Base):
    __tablename__ = "sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    exercise_id: Mapped[int] = mapped_column(Integer, ForeignKey("exercises.id"))
    reps: Mapped[int] = mapped_column(Integer, nullable=False)

    exercise: Mapped["Exercise"] = relationship("Exercise", back_populates="sets")