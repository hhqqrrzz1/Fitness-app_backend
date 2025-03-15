from typing import List
from pydantic import BaseModel, Field, EmailStr
from datetime import date

class CreateUser(BaseModel):
    email: EmailStr
    username: str
    password: str

class CreateSet(BaseModel):
    weight_per_exe: float = Field(..., gt=0)
    reps: int = Field(..., gt=0)

class CreateExercise(BaseModel):
    exercise_name: str
    weight: float = Field(..., gt=0)
    sets: List[CreateSet]

class CreateMuscleGroup(BaseModel):
    group_name: str
    exercises: List[CreateExercise]

class CreateTraining(BaseModel):
    date: date
    muscle_groups: List[CreateMuscleGroup]