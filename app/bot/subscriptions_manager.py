import loguru
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database.models import Subscription, Group
from ..database.session import AsyncSessionLocal


class SubscriptionManager:
    """Клас для роботи з підписками чатів та кешуванням даних."""

    def __init__(self):
        self._cache: dict[int, dict[str, str]] = {}

    async def load_cache(self):
        """Завантажує всі підписки з БД у пам'ять."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription).options(selectinload(Subscription.group))
            )
            subscriptions = result.scalars().all()

        self._cache = {
            sub.chat_id: {
                "group_name": sub.group.name,
                "week_type": sub.week_type
            } for sub in subscriptions
        }
        loguru.logger.info(f"Loaded {len(self._cache)} subscriptions into cache.")

    async def get_group(self, chat_id: int) -> str | None:
        """Повертає назву групи користувача.
        Спершу перевіряє кеш, якщо нема — звертається до БД."""
        user_data = self._cache.get(chat_id)
        if user_data:
            return user_data.get("group_name")

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription)
                .options(selectinload(Subscription.group))
                .where(Subscription.chat_id == chat_id)
            )
            subscription = result.scalars().first()

        if subscription:
            group_name = subscription.group.name
            self._cache.setdefault(chat_id, {})["group_name"] = group_name
            return group_name

        return None

    async def get_week_type(self, chat_id: int) -> str | None:
        """Повертає тип тижня користувача (numerator/denominator).
        Спершу перевіряє кеш, якщо нема — звертається до БД."""
        user_data = self._cache.get(chat_id)
        if user_data:
            return user_data.get("week_type")

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription).where(Subscription.chat_id == chat_id)
            )
            subscription = result.scalars().first()

        if subscription:
            week_type = subscription.week_type
            self._cache.setdefault(chat_id, {})["week_type"] = week_type
            return week_type

        return None

    async def set_group(self, chat_id: int, group_name: str, week_type: str = "numerator"):
        """Встановлює або оновлює підписку чату.
        Оновлює кеш та базу даних."""
        self._cache.setdefault(chat_id, {})["group_name"] = group_name
        self._cache[chat_id]["week_type"] = week_type

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
                subscription.week_type = week_type
            else:
                subscription = Subscription(chat_id=chat_id, group_id=group.id, week_type=week_type)
                session.add(subscription)
            await session.commit()

    async def set_week_type(self, chat_id: int, week_type: str):
        """Оновлює тільки тип тижня користувача.
        Оновлює кеш та БД."""
        self._cache.setdefault(chat_id, {})["week_type"] = week_type

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Subscription).where(Subscription.chat_id == chat_id))
            subscription = result.scalars().first()
            if subscription:
                subscription.week_type = week_type
                await session.commit()

    async def remove_group(self, chat_id: int) -> str | None:
        """Видаляє підписку чату.Оновлює кеш та базу даних.
        Повертає назву групи або None, якщо підписки не було."""
        user_data = self._cache.pop(chat_id, None)
        if user_data:
            group_name = user_data.get("group_name")
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(Subscription).where(Subscription.chat_id == chat_id))
                subscription = result.scalars().first()
                if subscription:
                    await session.delete(subscription)
                    await session.commit()
            return group_name
        return None
