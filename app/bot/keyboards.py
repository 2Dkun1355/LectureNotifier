from aiogram import types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.future import select
from ..database.models import Group
from ..database.session import AsyncSessionLocal


class Keyboards:
    @staticmethod
    async def group_keyboard(active_group: str | None = None, page: int = 0, buttons_per_page: int = 20,
                             buttons_per_row: int = 4, mode: str = 'main') -> types.InlineKeyboardMarkup:
        """Клавіатура для вибору груп з пагінацією і кнопкою повернутися."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Group.name).order_by(Group.name))
            groups = result.scalars().all()

        start = page * buttons_per_page
        end = start + buttons_per_page
        page_items = groups[start:end]

        keyboard = InlineKeyboardBuilder()
        for group_name in page_items:
            text = f"✅ {group_name}" if group_name == active_group else group_name
            keyboard.button(text=text, callback_data=f"subscribe:{group_name}")
        keyboard.adjust(buttons_per_row)

        nav_buttons = []
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page:{page - 1}:{mode}"))
        if end < len(groups):
            nav_buttons.append(types.InlineKeyboardButton(text="➡️ Вперед", callback_data=f"page:{page + 1}:{mode}"))
        if nav_buttons:
            keyboard.row(*nav_buttons)

        if mode == "setting":
            keyboard.row(Keyboards.back_keyboard())

        return keyboard.as_markup()

    @staticmethod
    async def settings_keyboard(active_group: str | None = None) -> types.InlineKeyboardMarkup:
        """Основне меню налаштувань."""
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🏫 Вибір групи", callback_data="settings:group")
        keyboard.button(text="📅 Тип тижня", callback_data="settings:week_type")
        # keyboard.button(text="🔔 Сповіщення", callback_data="settings:notifications")
        # keyboard.button(text="⚙️ Інші параметри", callback_data="settings:other")
        if active_group:
            keyboard.row(types.InlineKeyboardButton(text="❌ Скасувати підписку", callback_data="unsubscribe"))
        keyboard.adjust(2)
        return keyboard.as_markup()

    @staticmethod
    async def week_type_keyboard(active_week_type: str = None) -> types.InlineKeyboardMarkup:
        """Клавіатура для вибору типу тижня."""
        keyboard = InlineKeyboardBuilder()

        numerator_text = "✅ Чисельник" if active_week_type == "numerator" else "Чисельник"
        denominator_text = "✅ Знаменник" if active_week_type == "denominator" else "Знаменник"

        keyboard.button(text=numerator_text, callback_data="week_type:numerator")
        keyboard.button(text=denominator_text, callback_data="week_type:denominator")

        keyboard.row(Keyboards.back_keyboard())
        keyboard.adjust(2)
        return keyboard.as_markup()

    @staticmethod
    def back_keyboard() -> types.InlineKeyboardButton:
        """Клавіатура для повернення."""
        return types.InlineKeyboardButton(
            text="◀️ Повернутися",
            callback_data="settings:back"
        )
