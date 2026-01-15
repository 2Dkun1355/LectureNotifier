import json

from aiogram.filters import Command
from aiogram import types
from .utils import require_subscription, format_schedule


class CommandHandlers:
    """Хендлери для команд /start, /week тощо."""

    def __init__(self, dispatcher, keyboards, subscribe_manager, schedule_service):
        self.dispatcher = dispatcher
        self.keyboards = keyboards
        self.subscribe_manager = subscribe_manager
        self.schedule_service = schedule_service

        self._register_command_handlers()

    def _register_command_handlers(self):
        commands = [
            ("start", self.command_start),
            ("change", self.command_settings),
            ("today", self.command_today),
            ("week", self.command_week)
        ]
        for cmd_name, handler in commands:
            self.dispatcher.message.register(handler, Command(cmd_name))

    @require_subscription
    async def command_start(self, message: types.Message, user_data, *args, **kwargs):
        """Обробляє команду /start."""
        await message.answer(f"Привіт! Ти підписаний на групу {user_data["group_name"]}")

    @require_subscription
    async def command_settings(self, message: types.Message, *args, **kwargs):
        """Обробляє команду /settings для зміни групи."""
        markup = await self.keyboards.settings_keyboard()
        await message.answer("Меню налаштувань:", reply_markup=markup)

    @require_subscription
    async def command_today(self, message: types.Message, user_data, *args, **kwargs):
        """Відправляє розклад на сьогодні."""
        schedule = await self.schedule_service.get_today_schedule(group_name=user_data["group_name"], week_type=user_data["week_type"])
        message_text = await format_schedule(schedule=schedule, week_type=user_data["week_type"])
        await message.answer(message_text)

    @require_subscription
    async def command_week(self, message: types.Message, user_data, *args, **kwargs):
        """Відправляє розклад на тиждень."""
        schedule = await self.schedule_service.get_week_schedule(group_name=user_data["group_name"], week_type=user_data["week_type"])
        message_text = await format_schedule(schedule=schedule, week_type=user_data["week_type"])
        await message.answer(message_text)
