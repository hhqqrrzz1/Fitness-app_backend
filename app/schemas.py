from typing import List
from pydantic import BaseModel, Field
from datetime import date

class CreateUser(BaseModel):
    email: str
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

class SetResponse(BaseModel):
    id: int
    exercise_id: int
    weight_per_exe: float
    reps: int

    class Config:
        from_attributes = True

class ExerciseResponse(BaseModel):
    id: int
    muscle_group_id: int
    exercise_name: str
    weight: float
    numbers_reps: int
    sets: List[SetResponse]

    class Config:
        from_attributes = True
