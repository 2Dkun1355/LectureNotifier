import asyncio

from aiogram import Bot, Dispatcher
from loguru import logger

from .command import CommandHandlers
from .subscriptions_manager import SubscriptionManager
from .schedule_service import ScheduleService
from .keyboards import Keyboards
from .сallback import CallbackHandlers


class NotifierBot:
    """Telegram bot для розкладу та підписок."""
    def __init__(self, token: str):
        """Ініціалізація бота, диспетчера та сервісів."""
        self.bot = Bot(token=token)
        self.dispatcher = Dispatcher(bot=self.bot)
        self.subscribe_manager = SubscriptionManager()
        self.schedule_service = ScheduleService()

        self.keyboards = Keyboards()
        self.command_handlers = CommandHandlers(self.dispatcher, self.keyboards, self.subscribe_manager, self.schedule_service)
        self.callback_handlers = CallbackHandlers(self.dispatcher, self.keyboards, self.subscribe_manager)

    async def _background_sync_cache(self, interval: int = 300):
        """Фонове оновлення кешу кожні `interval` секунд (за замовчуванням 5 хв)."""
        while True:
            try:
                logger.info("Starting cache synchronization...")
                await self.subscribe_manager.load_cache()
                await self.schedule_service.load_cache()
                logger.info(f"Next synchronization in {interval} seconds.")
            except Exception as e:
                logger.error(f"Error during cache synchronization: {e}")
            await asyncio.sleep(interval)

    async def run(self):
        """Запускає бота."""
        logger.info("Bot started")

        asyncio.create_task(self._background_sync_cache())

        await self.dispatcher.start_polling(self.bot)
        await self.bot.session.close()
        logger.info("Bot stopped")
