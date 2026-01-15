from functools import wraps
from aiogram import types


def require_subscription(func):
    """Декоратор для перевірки підписки на групу."""

    @wraps(func)
    async def wrapper(self, message: types.Message, *args, **kwargs):
        user_data = await self.subscribe_manager.get_user(message.chat.id)
        if not user_data:
            markup = await self.keyboards.group_keyboard(mode="start")
            await message.answer("Привіт! Обери групу для підписки:", reply_markup=markup)
            return
        return await func(self, message=message, user_data=user_data)

    return wrapper


DAYS = {0: "Понеділок", 1: "Вівторок", 2: "Середа", 3: "Четвер",
        4: "Пʼятниця", 5: "Субота", 6: "Неділя"}
WEEK_MAP = {"numerator": "чис.", "denominator": "знам."}


async def format_lesson(lesson) -> str:
    """Форматує один урок у рядок для Telegram."""
    return (
        f"{lesson.lesson_number or '-'}. {lesson.subject or 'Не вказано'} | "
        f"{lesson.start_time or '--:--'} - {lesson.end_time or '--:--'} | "
        f"{lesson.teacher or 'Не вказано'} | "
        f"{lesson.room or '-'}"
    )


async def format_schedule(schedule: dict[int, list[dict]], week_type: str) -> str:
    """Форматує словник розкладу на тиждень або день у рядок для Telegram."""
    if not schedule:
        return "😱 Занять немає."

    text_lines = [f"Розклад ({WEEK_MAP.get(week_type)})\n"]
    for day, lessons in sorted(schedule.items()):
        text_lines.append(f"{DAYS.get(day)}:")
        for lesson in lessons:
            text_lines.append(await format_lesson(lesson))
        text_lines.append("")

    return "\n".join(text_lines).strip()
