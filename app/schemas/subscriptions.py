from pydantic import BaseModel
from .groups import ReadGroup


class CreateSubscription(BaseModel):
    user_id: int
    week_type: str
    group: ReadGroup | None

class UpdateSubscription(BaseModel):
    week_type: str
    group: ReadGroup | None
    is_active: bool

class ReadSubscription(BaseModel):
    user_id: int
    id: int
    week_type: str
    is_active: bool
    group: ReadGroup | None


