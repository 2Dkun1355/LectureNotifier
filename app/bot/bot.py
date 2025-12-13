import json

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from loguru import logger

from .subscriptions_manager import SubscriptionManager
from .schedule_service import ScheduleService
from .keyboards import Keyboards
from .utils import require_subscription


class NotifierBot:
    """Telegram bot для розкладу та підписок."""
    def __init__(self, token: str):
        """Ініціалізація бота, диспетчера та сервісів."""
        self.bot = Bot(token=token)
        self.dispatcher = Dispatcher(bot=self.bot)
        self.subscribe_manager = SubscriptionManager()
        self.schedule_service = ScheduleService()

        self.subscribers = {}

        self._register_command_handlers()
        self._register_callback_handlers()

    def _register_command_handlers(self):
        """Реєстрація команд."""
        self.dispatcher.message.register(self.handle_start, Command("start"))
        self.dispatcher.message.register(self.handle_change, Command("change"))
        self.dispatcher.message.register(self.handle_today, Command("today"))
        self.dispatcher.message.register(self.handle_week, Command("week"))

    def _register_callback_handlers(self):
        """Реєстрація колбеків."""
        self.dispatcher.callback_query.register(self.handle_subscription, lambda c: c.data.startswith("subscribe"))
        self.dispatcher.callback_query.register(self.handle_unsubscribe, lambda c: c.data.startswith("unsubscribe"))
        self.dispatcher.callback_query.register(self.handle_group_pagination, lambda c: c.data.startswith("page"))
        self.dispatcher.callback_query.register(self.handle_back, lambda c: c.data == "settings:back")
        self.dispatcher.callback_query.register(self.handle_setting_action, lambda c: c.data.startswith("settings"))
        self.dispatcher.callback_query.register(self.handle_week_type, lambda c: c.data.startswith("week_type"))

    async def handle_start(self, message: types.Message):
        """Обробляє команду /start."""
        active_group = await self.subscribe_manager.get_group(message.chat.id)
        markup = await Keyboards.group_keyboard(active_group=active_group, show_back=False)
        if active_group:
            await message.answer(f"Привіт! Ти підписаний на групу {active_group}")
        else:
            await message.answer("Привіт! Обери групу для підписки:", reply_markup=markup)

    @require_subscription
    async def handle_change(self, message: types.Message):
        """Обробляє команду /change для зміни групи."""
        active_group = await self.subscribe_manager.get_group(message.chat.id)
        markup = await Keyboards.settings_keyboard(active_group)
        await message.answer("Меню налаштувань:", reply_markup=markup)

    async def handle_group_pagination(self, callback: types.CallbackQuery):
        """Обробляє пагінацію вибору груп."""
        page = int(callback.data.split(":")[1])
        active_group = await self.subscribe_manager.get_group(callback.message.chat.id)
        markup = await Keyboards.group_keyboard(active_group=active_group, page=page, show_back=True)
        await callback.message.edit_reply_markup(reply_markup=markup)
        await callback.answer()

    async def handle_back(self, callback: types.CallbackQuery):
        """Повертає до меню налаштувань."""
        active_group = await self.subscribe_manager.get_group(callback.message.chat.id)
        markup = await Keyboards.settings_keyboard(active_group)
        await callback.message.edit_text("Меню налаштувань:", reply_markup=markup)
        await callback.answer()

    async def handle_setting_action(self, callback: types.CallbackQuery):
        """Обробляє дії в меню налаштувань."""
        action = callback.data.split(":")[1]
        active_group = await self.subscribe_manager.get_group(callback.message.chat.id)
        if action == "group":
            markup = await Keyboards.group_keyboard(active_group=active_group, show_back=True)
            await callback.message.edit_text("Оберіть нову групу:", reply_markup=markup)

        elif action == "week_type":
            markup = await Keyboards.week_type_keyboard()
            await callback.message.edit_text("Оберіть тип тижня:", reply_markup=markup)

        else:
            await callback.message.edit_text("Це можливо колись запрацює")

        await callback.answer()

    async def handle_week_type(self, callback: types.CallbackQuery):
        """Обробляє вибір типу тижня."""
        await callback.message.answer("Ця функція поки не реалізована.")
        await callback.answer()

    async def handle_subscription(self, callback: types.CallbackQuery):
        """Обробляє підписку на групу."""
        group = callback.data.split(":")[1]
        await self.subscribe_manager.set_group(callback.message.chat.id, group)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"✅ Чат підписаний на групу: {group}")
        await callback.answer()

    async def handle_unsubscribe(self, callback: types.CallbackQuery):
        """Скасовує підписку на групу."""
        group = await self.subscribe_manager.remove_group(callback.message.chat.id)
        if group:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer("Підписка скасована ✅")
        else:
            await callback.message.answer("Підписки не знайдено.")
        await callback.answer()

    @require_subscription
    async def handle_today(self, message: types.Message):
        """Відправляє розклад на сьогодні."""
        await message.answer(await self.schedule_service.today_schedule(message.chat.id))

    @require_subscription
    async def handle_week(self, message: types.Message):
        """Відправляє розклад на тиждень."""
        await message.answer(await self.schedule_service.week_schedule(message.chat.id))

    async def run(self):
        """Запускає бота."""
        logger.info("Bot started")
        self.subscribers = await self.subscribe_manager.get_subscribers()
        # logger.info(json.dumps(self.subscribers, indent=4, ensure_ascii=False))
        await self.dispatcher.start_polling(self.bot)
        await self.bot.session.close()
        logger.info("Bot stopped")
