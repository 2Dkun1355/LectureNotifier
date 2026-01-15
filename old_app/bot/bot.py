import asyncio
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from old_app.bot.utils import format_lesson


class NotifierBot:
    """Telegram bot для розкладу та підписок."""

    def __init__(self, bot, dispatcher, subscribe_service, schedule_service):
        """Ініціалізація бота, диспетчера та сервісів."""
        self.bot = bot
        self.dispatcher = dispatcher

        self.subscribe_service = subscribe_service
        self.schedule_service = schedule_service

        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()

    async def send_lesson_messages(self, group_name: str, week_type: str, lesson_id: int):
        users_ids = await self.subscribe_service.get_users_from_options(group_name, week_type)

        if users_ids is None:
            return

        lesson = await self.schedule_service.get_lesson(lesson_id)

        for user_id in users_ids:
            text = await format_lesson(lesson)
            await  self.bot.send_message(chat_id=user_id, text=f"Наступна пара:\n{text}")

    async def _ggg(self):
        schedules = await self.schedule_service.get_test_data()
        for group_name, schedule in schedules.items():
            for lesson in schedule:
                hour, minute = map(int, lesson.start_time.split(":"))
                day_of_week = lesson.day_of_week
                job_id = f"{group_name}:{lesson.week_type}:{lesson.id}"
                self.scheduler.add_job(
                    self.send_lesson_messages,
                    trigger="cron",
                    id=job_id,
                    day_of_week=day_of_week,
                    hour=hour,
                    minute=minute - 5,
                    args=[group_name, lesson.week_type, lesson.id],
                )

    # async def _background_sync_cache(self, interval: int = 12 * 60 * 60):
    #     """Фонове оновлення кешу кожні `interval` секунд"""
    #     while True:
    #         try:
    #             logger.info("Starting cache synchronization...")
    #             await self.subscribe_service.load_cache()
    #             await self.schedule_service.load_cache()
    #             logger.info(f"Next synchronization in {interval // (60 * 60)} hours.")
    #             await self._ggg()
    #         except Exception as e:
    #             logger.error(f"Error during cache synchronization and try again: {e}")
    #             continue
    #         await asyncio.sleep(interval)

    async def run(self):
        """Запускає бота."""
        logger.info("Bot started")

        await self.subscribe_service.load_cache()
        await self.schedule_service.load_cache()

        await self._ggg()

        await self.dispatcher.start_polling(self.bot)
        await self.bot.session.close()

        logger.info("Bot stopped")
