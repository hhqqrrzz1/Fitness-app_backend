from typing import List
from pydantic import BaseModel
from datetime import date
from enum import Enum

class CreateUser(BaseModel):
    email: str
    username: str
    password: str

class MuscleGroupName(Enum):
    BICEPS = 'Бицепс'
    TRICEPS = 'Трицепс'
    CHEST = "Грудь"
    BACK = "Спина"
    SHOULDERS = "Плечи"
    LEGS = "Ноги"

class CreateSet(BaseModel):
    weight_per_exe: int
    reps: int

class CreateExercise(BaseModel):
    exercise_name: str
    weight: int
    sets: List[CreateSet]

class CreateMuscleGroup(BaseModel):
    group_name: MuscleGroupName
    exercises: List[CreateExercise]

class CreateTraining(BaseModel):
    date: date
    muscle_groups: List[CreateMuscleGroup]