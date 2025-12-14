from aiogram import types

class CallbackHandlers:
    """Хендлери для callback query."""

    def __init__(self, dispatcher, keyboards, subscribe_manager):
        self.dispatcher = dispatcher
        self.keyboards = keyboards
        self.subscribe_manager = subscribe_manager
        self._register_callback_handlers()

    def _register_callback_handlers(self):
        """Реєстрація колбеків."""
        self.dispatcher.callback_query.register(self.handle_subscription, lambda c: c.data.startswith("subscribe"))
        self.dispatcher.callback_query.register(self.handle_unsubscribe, lambda c: c.data.startswith("unsubscribe"))
        self.dispatcher.callback_query.register(self.handle_group_pagination, lambda c: c.data.startswith("page"))
        self.dispatcher.callback_query.register(self.handle_setting_action, lambda c: c.data.startswith("settings"))
        self.dispatcher.callback_query.register(self.handle_change_week_type, lambda c: c.data.startswith("week_type"))

    async def handle_group_pagination(self, callback: types.CallbackQuery):
        """Обробляє пагінацію вибору груп."""
        _, page, mode = callback.data.split(":")
        active_group = await self.subscribe_manager.get_group(callback.message.chat.id)
        markup = await self.keyboards.group_keyboard(active_group=active_group, page=int(page), mode=mode)
        await callback.message.edit_reply_markup(reply_markup=markup)
        await callback.answer()

    async def handle_setting_action(self, callback: types.CallbackQuery):
        """Обробляє дії в меню налаштувань."""
        action = callback.data.split(":")[1]

        handlers = {
            "group": self._handle_group,
            "week_type": self._handle_week_type,
            "back": self._handle_back_to_settings,
        }

        handler = handlers.get(action, self._handle_unknown_action)
        await handler(callback)
        await callback.answer()

    async def _handle_group(self, callback: types.CallbackQuery):
        active_group = await self.subscribe_manager.get_group(callback.message.chat.id)
        markup = await self.keyboards.group_keyboard(active_group=active_group, mode="setting")
        await callback.message.edit_text("Оберіть нову групу:", reply_markup=markup)

    async def _handle_week_type(self, callback: types.CallbackQuery):
        active_get_week_type = await self.subscribe_manager.get_week_type(callback.message.chat.id)
        markup = await self.keyboards.week_type_keyboard(active_get_week_type)
        await callback.message.edit_text("Оберіть тип тижня:", reply_markup=markup)

    async def _handle_back_to_settings(self, callback: types.CallbackQuery):
        active_group = await self.subscribe_manager.get_group(callback.message.chat.id)
        markup = await self.keyboards.settings_keyboard(active_group)
        await callback.message.edit_text("Меню налаштувань:", reply_markup=markup)

    async def _handle_unknown_action(self, callback: types.CallbackQuery):
        await callback.message.edit_text("Це можливо колись запрацює")

    async def handle_change_week_type(self, callback: types.CallbackQuery):
        """Обробляє зміну типу тиждня."""
        week_type = callback.data.split(":")[1]
        await self.subscribe_manager.set_week_type(callback.message.chat.id, week_type)
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(f"✅ Тип тиждня змінений на ...")
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