from aiogram.filters import Command
from aiogram import types
from .utils import require_subscription


class CommandHandlers:
    """Хендлери для команд /start, /week тощо."""

    def __init__(self, dispatcher, keyboards, subscribe_manager, schedule_service):
        self.dispatcher = dispatcher
        self.keyboards = keyboards
        self.subscribe_manager = subscribe_manager
        self.schedule_service = schedule_service
        self._register_command_handlers()

    def _register_command_handlers(self):
        """Реєстрація команд."""
        self.dispatcher.message.register(self.command_start, Command("start"))
        self.dispatcher.message.register(self.command_settings, Command("change"))
        self.dispatcher.message.register(self.command_today, Command("today"))
        self.dispatcher.message.register(self.command_week, Command("week"))

    async def command_start(self, message: types.Message):
        """Обробляє команду /start."""
        active_group = await self.subscribe_manager.get_group(message.chat.id)
        markup = await self.keyboards.group_keyboard(active_group=active_group, mode="start")
        if active_group:
            await message.answer(f"Привіт! Ти підписаний на групу {active_group}")
        else:
            await message.answer("Привіт! Обери групу для підписки:", reply_markup=markup)

    @require_subscription
    async def command_settings(self, message: types.Message):
        """Обробляє команду /settings для зміни групи."""
        active_group = await self.subscribe_manager.get_group(message.chat.id)
        markup = await self.keyboards.settings_keyboard(active_group)
        await message.answer("Меню налаштувань:", reply_markup=markup)

    @require_subscription
    async def command_today(self, message: types.Message):
        """Відправляє розклад на сьогодні."""
        week_type = await self.subscribe_manager.get_week_type(message.chat.id)
        group_name = await self.subscribe_manager.get_group(message.chat.id)
        await message.answer(await self.schedule_service.today_schedule(group_name, week_type))

    @require_subscription
    async def command_week(self, message: types.Message):
        """Відправляє розклад на тиждень."""
        week_type = await self.subscribe_manager.get_week_type(message.chat.id)
        group_name = await self.subscribe_manager.get_group(message.chat.id)
        await message.answer(await self.schedule_service.week_schedule(group_name, week_type))
