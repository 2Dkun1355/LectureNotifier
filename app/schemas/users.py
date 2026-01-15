from pydantic import BaseModel
from .subscriptions import ReadSubscription


class CreateUser(BaseModel):
    chat_id: int
    username: str
    first_name: str
    last_name: str

class UpdateUser(BaseModel):
    username: str
    first_name: str
    last_name: str

class ReadUser(BaseModel):
    id: int
    chat_id: int
    username: str
    first_name: str
    last_name: str
    subscription: ReadSubscription | None
