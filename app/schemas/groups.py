from pydantic import BaseModel

class BaseGroup(BaseModel):
    name: str
    specialty: str
    course: int

class ReadGroup(BaseModel):
    id: int
    name: str
    specialty: str
    course: int
