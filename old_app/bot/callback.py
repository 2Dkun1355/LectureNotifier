from functools import partial
from aiogram import types

class CallbackHandlers:
    """Хендлери для callback query."""

    def __init__(self, dispatcher, keyboards, subscribe_manager):
        self.dispatcher = dispatcher
        self.keyboards = keyboards
        self.subscribe_manager = subscribe_manager

        self._register_callback_handlers()

    def _register_callback_handlers(self, *args, **kwargs):
        """Реєстрація колбеків."""

        callbacks = [
            ("subscribe", self.handle_subscription),
            ("unsubscribe", self.handle_unsubscribe),
            ("page", self.handle_group_pagination),
            ("settings", self.handle_setting_action),
            ("week_type", self.handle_change_week_type),
        ]

        for key, handler in callbacks:
            checker = partial(self._check_callback_data, key=key)
            self.dispatcher.callback_query.register(handler, checker)

    @staticmethod
    def _check_callback_data(callback_query, key):
        return callback_query.data.startswith(key)

    async def handle_group_pagination(self, callback: types.CallbackQuery, *args, **kwargs):
        """Обробляє пагінацію вибору груп."""
        _, page, mode, active_group = callback.data.split(":")
        markup = await self.keyboards.group_keyboard(active_group=active_group, mode=mode, page=int(page))
        await callback.message.edit_reply_markup(reply_markup=markup)
        await callback.answer()

    async def handle_setting_action(self, callback: types.CallbackQuery, *args, **kwargs):
        """Обробляє дії в меню налаштувань."""
        _, action = callback.data.split(":")
        user_data = await self.subscribe_manager.get_user(callback.message.chat.id)
        handlers = {
            "group": self._handle_group,
            "week_type": self._handle_week_type,
            "back": self._handle_back_to_settings,
        }

        handler = handlers.get(action, self._handle_unknown_action)
        await handler(callback=callback, user_data=user_data)
        await callback.answer()

    async def _handle_group(self, callback: types.CallbackQuery, user_data, *args, **kwargs):
        markup = await self.keyboards.group_keyboard(active_group=user_data.get("group_name"), mode="setting")
        await callback.message.edit_text("Оберіть нову групу:", reply_markup=markup)

    async def _handle_week_type(self, callback: types.CallbackQuery, user_data, *args, **kwargs):
        markup = await self.keyboards.week_type_keyboard(user_data.get("week_type"))
        await callback.message.edit_text("Оберіть тип тижня:", reply_markup=markup)

    async def _handle_back_to_settings(self, callback: types.CallbackQuery, *args, **kwargs):
        markup = await self.keyboards.settings_keyboard()
        await callback.message.edit_text("Меню налаштувань:", reply_markup=markup)

    async def _handle_unknown_action(self, callback: types.CallbackQuery, *args, **kwargs):
        await callback.message.edit_text("Це можливо колись запрацює")

    async def handle_change_week_type(self, callback: types.CallbackQuery):
        """Обробляє зміну типу тиждня."""
        _, week_type, week_type_from_user = callback.data.split(":")
        await self.subscribe_manager.set_week_type(callback.message.chat.id, week_type)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"✅ Тип тиждня змінений на {week_type_from_user}")
        await callback.answer()

    async def handle_subscription(self, callback: types.CallbackQuery):
        """Обробляє підписку на групу."""
        _, group = callback.data.split(":")
        await self.subscribe_manager.set_group(callback.message.chat.id, group)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"✅ Чат підписаний на групу: {group}")
        await callback.answer()

    async def handle_unsubscribe(self, callback: types.CallbackQuery):
        """Скасовує підписку на групу."""
        group = await self.subscribe_manager.remove_user(callback.message.chat.id)
        if group:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.answer(f"Підписка на {group} скасована ✅")
        else:
            await callback.message.answer("Підписки не знайдено 🤯")
        await callback.answer()