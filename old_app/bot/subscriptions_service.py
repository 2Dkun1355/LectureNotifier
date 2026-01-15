from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database.models import Subscription, Group
from ..database.session import AsyncSessionLocal


class SubscriptionService:
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

    async def get_users_from_options(self, group_name, week_type) -> list:
        """Повертає всі підписки користувачів."""
        users_ids = []
        for chat_id, data in self._cache.items():
            if data["group_name"] == group_name and data["week_type"] == week_type:
                users_ids.append(chat_id)
        return users_ids

    async def get_user(self, chat_id: int, *args, **kwargs) -> dict | None:
        """Повертає дані користувача (підписку) з кешу або БД."""
        if chat_id in self._cache:
            return self._cache[chat_id]

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription).where(Subscription.chat_id == chat_id).options(selectinload(Subscription.group))
            )
            subscription = result.scalars().first()
            if not subscription:
                return None

            data = {
                "group_name": subscription.group.name,
                "week_type": subscription.week_type
            }
            self._cache[chat_id] = data
            return data

    async def set_group(self, chat_id: int, group_name: str, week_type: str | None = None, *args, **kwargs):
        """Встановлює або оновлює підписку чату.
        Оновлює кеш та базу даних."""
        async with AsyncSessionLocal() as session:
            group = await session.scalar(select(Group).where(Group.name == group_name))

            subscription = await session.scalar(select(Subscription).where(Subscription.chat_id == chat_id))
            final_week_type = week_type or (subscription.week_type if subscription else "numerator")

            if subscription:
                subscription.group_id = group.id
                subscription.week_type = final_week_type
            else:
                subscription = Subscription(chat_id=chat_id, group_id=group.id, week_type=final_week_type)
                session.add(subscription)

            await session.commit()

        self._cache[chat_id] = {
            "group_name": group_name,
            "week_type": final_week_type
        }

    async def set_week_type(self, chat_id: int, week_type: str, *args, **kwargs):
        """Оновлює тільки тип тижня користувача.
        Оновлює кеш та БД."""
        self._cache.setdefault(chat_id, {})["week_type"] = week_type

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription).where(Subscription.chat_id == chat_id)
            )
            subscription = result.scalars().first()
            if subscription:
                subscription.week_type = week_type
                await session.commit()

    async def remove_user(self, chat_id: int, ) -> str | None:
        """Видаляє підписку чату. Оновлює кеш та базу даних.
        Повертає назву групи або None, якщо підписки не було."""
        group_name = self._cache.get(chat_id).get("group_name")
        self._cache.pop(chat_id, None)

        async with AsyncSessionLocal() as session:
            subscription = await session.scalar(select(Subscription).where(Subscription.chat_id == chat_id))
            if not subscription:
                return None
            await session.delete(subscription)
            await session.commit()

        return group_name
