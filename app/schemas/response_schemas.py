from typing import List
from pydantic import BaseModel
from datetime import date

class SetResponse(BaseModel):
    id: int
    weight_per_exe: float
    reps: int

    class Config:
        from_attributes = True

class ExerciseResponse(BaseModel):
    id: int
    exercise_name: str
    weight: float
    numbers_reps: int
    sets: List[SetResponse]

    class Config:
        from_attributes = True

class MuscleGroupResponse(BaseModel):
    id: int
    group_name: str
    exercises: List[ExerciseResponse]

    class Config:
        from_attributes = True

class TrainingResponse(BaseModel):
    id: int
    title: str
    muscle_groups: List[MuscleGroupResponse]

    class Config:
        from_attributes = True
