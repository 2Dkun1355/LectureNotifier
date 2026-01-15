from sqlalchemy import Column, String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)

    subscription = relationship("Subscription", back_populates="users")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    week_type = Column(String, nullable=True)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", back_populates="subscriptions")

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="subscriptions")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    subscriptions = relationship("Subscription", back_populates="group")
    lessons = relationship("Lesson", back_populates="group")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)

    week_day = Column(Integer, nullable=False)
    lesson_number = Column(Integer, nullable=False)
    week_type = Column(String, nullable=False)

    subject = Column(String)
    teacher = Column(String)
    room = Column(String)
    start_time = Column(String)
    end_time = Column(String)

    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    group = relationship("Group", back_populates="lessons")
