from datetime import datetime
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..database.models import Lesson, Subscription
from ..database.session import AsyncSessionLocal


class ScheduleService:
    """Сервіс для отримання розкладу занять."""
    DAYS = {1: "Понеділок", 2: "Вівторок", 3: "Середа", 4: "Четвер",
            5: "Пʼятниця", 6: "Субота", 7: "Неділя"}
    WEEK_MAP = {"numerator": "чис.", "denominator": "знам."}

    async def format_lesson(self, lesson: Lesson) -> str:
        """Форматує урок у рядок для Telegram."""
        return (
            f"{lesson.lesson_number}. {lesson.subject} | "
            f"{lesson.start_time or "--:--"} - {lesson.end_time or "--:--"} | "
            f"{lesson.teacher or "Не вказано"} | "
            f"{lesson.room or '-'}"
        )

    async def today_schedule(self, chat_id: int, week_type: str = "denominator") -> str:
        """Повертає текст розкладу на сьогодні для чату за week_type."""
        weekday = datetime.today().isoweekday()

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription)
                .where(Subscription.chat_id == chat_id)
                .options(selectinload(Subscription.group))
            )
            subscription = result.scalars().first()

            group = subscription.group

            result = await session.execute(
                select(Lesson)
                .where(
                    Lesson.group_id == group.id,
                    Lesson.week_day == weekday,
                    Lesson.week_type == week_type
                )
                .order_by(Lesson.lesson_number)
            )
            lessons = result.scalars().all()

        if not lessons:
            return f"Сьогодні немає занять."

        formatted = [f"Розклад на сьогодні:\n"]
        formatted += [await self.format_lesson(lesson) for lesson in lessons]
        return "\n".join(formatted)

    async def week_schedule(self, chat_id: int, week_type: str = "denominator") -> str:
        """Повертає текстовий розклад на тиждень для чату за week_type."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Subscription)
                .where(Subscription.chat_id == chat_id)
                .options(selectinload(Subscription.group))
            )
            subscription = result.scalars().first()

            group = subscription.group

            result = await session.execute(
                select(Lesson)
                .where(
                    Lesson.group_id == group.id,
                    Lesson.week_type == week_type
                )
                .order_by(Lesson.week_day, Lesson.lesson_number)
            )
            lessons = result.scalars().all()

        if not lessons:
            return "Немає занять."

        output = [f"Розклад на тиждень:"]
        current_day = None
        for lesson in lessons:
            if current_day != lesson.week_day:
                current_day = lesson.week_day
                output.append(f"\n{self.DAYS.get(current_day)}:\n")
            output.append(await self.format_lesson(lesson))

        return "\n".join(output)
