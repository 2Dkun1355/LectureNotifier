from datetime import time
from pydantic import BaseModel

class CreateLesson(BaseModel):
    week_day: int
    lesson_number: int
    week_type: int
    subject: str
    teacher: str
    room: str
    group_id: int
    start_time: time
    end_time: time

class UpdateLesson(BaseModel):
    lesson_number: int
    subject: str
    teacher: str
    room: str
    start_time: time
    end_time: time

