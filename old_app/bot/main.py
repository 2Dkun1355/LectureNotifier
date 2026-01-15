from aiogram import Bot, Dispatcher
from loguru import logger

from .bot import NotifierBot
from .keyboards import Keyboards
from .command import CommandHandlers
from .callback import CallbackHandlers
from .subscriptions_service import SubscriptionService
from .schedule_service import ScheduleService
from ..database import init_db


async def bot_init(token):
    await init_db()
    bot = Bot(token)
    dispatcher = Dispatcher()

    keyboards = Keyboards()
    subscribe_service = SubscriptionService()
    schedule_service = ScheduleService()

    CommandHandlers(
        dispatcher=dispatcher,
        keyboards=keyboards,
        subscribe_manager=subscribe_service,
        schedule_service=schedule_service,
    )

    CallbackHandlers(
        dispatcher=dispatcher,
        keyboards=keyboards,
        subscribe_manager=subscribe_service,
    )

    app = NotifierBot(
        bot=bot,
        dispatcher=dispatcher,
        subscribe_service=subscribe_service,
        schedule_service=schedule_service,
    )

    try:
        await app.run()
    except Exception as e:
        logger.error(f"Bot error: {e}")


