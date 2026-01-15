from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

class Repository:
    def __init__(self, model, session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def create(self, **kwargs) -> None:
        user = self.model(**kwargs)
        self.session.add(user)
        await self.session.commit()

    async def get_from_id(self, item_id: int):
        stmt = select(self.model).where(self.model.id == item_id)

        user = await self.session.scalars(stmt)
        return user.one_or_none()

    async def get_all(self):
        stmt = select(self.model)
        users = await self.session.scalars(stmt)
        return users.all()

    async def update(self, item_id: int, **kwargs) -> None:
        stmt = update(self.model).where(self.model.id == item_id).values(**kwargs)

        await self.session.execute(stmt)
        await self.session.commit()

    async def delete(self, item_id: int) -> None:
        stmt = delete(self.model).where(self.model.id == item_id)

        await self.session.execute(stmt)
        await self.session.commit()
