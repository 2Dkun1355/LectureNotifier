from functools import wraps
from aiogram import types

def require_subscription(func):
    """Декоратор для перевірки підписки на групу."""
    @wraps(func)
    async def wrapper(self, message: types.Message, *args, **kwargs):
        group = await self.subscribe_manager.get_group(message.chat.id)
        if not group:
            await message.answer("Спочатку підпишись на групу командою /start!")
            return
        return await func(self, message, *args, **kwargs)
    return wrapper