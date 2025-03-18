from typing import List
from pydantic import BaseModel, Field, EmailStr
from datetime import date

class CreateUser(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=1, max_length=20)
    password: str = Field(..., min_length=5)

class CreateSet(BaseModel):
    weight_per_exe: float = Field(..., ge=0)
    reps: int = Field(..., gt=0)

class CreateExercise(BaseModel):
    exercise_name: str = Field(..., min_length=3, max_length=15)
    weight: float = Field(..., ge=0)
    sets: List[CreateSet]

class CreateMuscleGroup(BaseModel):
    group_name: str = Field(..., min_length=3, max_length=15)
    exercises: List[CreateExercise]

class CreateTraining(BaseModel):
    date: date
    muscle_groups: List[CreateMuscleGroup]