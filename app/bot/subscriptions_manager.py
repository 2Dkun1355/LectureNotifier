from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from loguru import logger

from ..database.models import Subscription, Group, Lesson
from ..database.session import AsyncSessionLocal

class SubscriptionManager:
    """Клас для роботи з підписками в базі даних."""

    async def get_subscribers(self) -> dict[int, dict]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(
                    Subscription.chat_id,
                    Group.name,
                    Lesson.week_day,
                    Lesson.week_type,
                    Lesson.lesson_number,
                    Lesson.subject,
                    Lesson.teacher,
                    Lesson.room,
                    Lesson.start_time,
                    Lesson.end_time,
                )
                .join(Group, Subscription.group_id == Group.id)
                .join(Lesson, Lesson.group_id == Group.id)
            )
            rows = result.all()

        cache: dict[int, dict] = {}

        for chat_id, group_name, week_day, week_type, lesson_number, subject, teacher, room, start_time, end_time in rows:
            chat = cache.setdefault(chat_id, {
                "group_name": group_name,
                "lessons": {"numerator": {}, "denominator": {}},
            })

            lessons_by_type = chat["lessons"][week_type]
            lessons_by_type.setdefault(week_day, []).append({
                "lesson_number": lesson_number,
                "subject": subject,
                "teacher": teacher,
                "room": room,
                "start_time": start_time,
                "end_time": end_time,
            })

        return cache

    async def get_group(self, chat_id: int) -> str | None:
        """Повертає назву групи для даного chat_id або None."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription)
                .options(selectinload(Subscription.group))
                .where(Subscription.chat_id == chat_id)
            )
            subscription = result.scalars().first()
        if subscription:
            return subscription.group.name
        return None

    async def set_group(self, chat_id: int, group_name: str):
        """Встановлює або оновлює підписку чату на групу."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Group).where(Group.name == group_name))
            group = result.scalars().first()
            if not group:
                group = Group(name=group_name)
                session.add(group)
                await session.commit()
                await session.refresh(group)

            result = await session.execute(select(Subscription).where(Subscription.chat_id == chat_id))
            subscription = result.scalars().first()
            if subscription:
                subscription.group_id = group.id
            else:
                subscription = Subscription(chat_id=chat_id, group_id=group.id)
                session.add(subscription)
            await session.commit()
            logger.info(f"Chat {chat_id} subscription set to {group_name}")

    async def remove_group(self, chat_id: int) -> str | None:
        """Видаляє підписку чату. Повертає назву групи або None."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription)
                .options(selectinload(Subscription.group))
                .where(Subscription.chat_id == chat_id)
            )
            subscription = result.scalars().first()
            if subscription:
                group_name = subscription.group.name  # тепер безпечне звернення
                await session.delete(subscription)
                await session.commit()
                logger.info(f"Chat {chat_id} subscription removed")
                return group_name
        return None
