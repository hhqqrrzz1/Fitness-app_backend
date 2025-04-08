from pydantic import BaseModel
from datetime import date

class UpdateTrainings(BaseModel):
    training_id: int
    update_date: date