from typing import List
from pydantic import BaseModel
from datetime import date

class CreateUser(BaseModel):
    email: str
    username: str
    password: str

class CreateSet(BaseModel):
    weight_per_exe: int
    reps: int

class CreateExercise(BaseModel):
    exercise_name: str
    weight: int
    sets: List[CreateSet]
    numbers_reps: int

class CreateMuscleGroup(BaseModel):
    group_name: str
    exercises: List[CreateExercise]

class CreateTraining(BaseModel):
    date: date
    muscle_groups: List[CreateMuscleGroup]