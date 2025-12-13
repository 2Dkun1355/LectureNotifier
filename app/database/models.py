from sqlalchemy import Column, String, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Group(Base):
    """Таблиця груп"""
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    lessons = relationship("Lesson", back_populates="group", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="group", cascade="all, delete-orphan")


class Subscription(Base):
    """Підписки чатів"""
    __tablename__ = "subscriptions"

    chat_id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    group = relationship("Group", back_populates="subscriptions")


class Lesson(Base):
    """Модель розкладу"""
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    week_day = Column(Integer, nullable=False)
    lesson_number = Column(Integer, nullable=False)
    week_type = Column(String, nullable=False)
    subject = Column(String)
    teacher = Column(String)
    room = Column(String)
    start_time = Column(String)
    end_time = Column(String)

    group = relationship("Group", back_populates="lessons")

    __table_args__ = (
        PrimaryKeyConstraint("id"),
    )
