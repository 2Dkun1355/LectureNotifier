import json
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger
from config import BOT_TOKEN, REMINDER_BEFORE_MINUTES, TODAY_SCHEDULE_HOUR, TODAY_SCHEDULE_MINUTE, TODAY_SCHEDULE_DAYS, \
    WEEK_SCHEDULE_HOUR, WEEK_SCHEDULE_MINUTE, WEEK_SCHEDULE_DAY, REMINDERS_HOUR, REMINDERS_MINUTE, REMINDERS_DAY
from schedule import ScheduleParser


class NotifierBot:
    def __init__(self, parser: ScheduleParser = ScheduleParser()):
        self.bot = Bot(token=BOT_TOKEN)
        self.dispatcher = Dispatcher()
        self.parser = parser
        self.chat_subscriptions: dict[int, str] = {}
        self.scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")
        self._register_handlers()

    def _build_keyboard(self, page: int = 0, buttons_per_page: int = 20, buttons_per_row: int = 4,active_group: str | None = None):
        keyboard = InlineKeyboardBuilder()
        start_index = page * buttons_per_page
        end_index = start_index + buttons_per_page
        page_items = self.parser.groups[start_index:end_index]

        for group in page_items:
            text = f"✅ {group}" if group == active_group else group
            keyboard.button(text=text, callback_data=f"sub:{group}")

        navigation_buttons = []
        if page > 0:
            navigation_buttons.append(types.InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page:{page - 1}"))
        if end_index < len(self.parser.groups):
            navigation_buttons.append(types.InlineKeyboardButton(text="➡️ Вперед", callback_data=f"page:{page + 1}"))
        if navigation_buttons:
            keyboard.row(*navigation_buttons)

        keyboard.adjust(buttons_per_row)

        if active_group:
            keyboard.row(types.InlineKeyboardButton(text="❌ Скасувати підписку", callback_data="unsubscribe"))

        return keyboard.as_markup()

    def _register_handlers(self):
        self.dispatcher.message.register(self.handle_start, Command("start"))
        self.dispatcher.message.register(self.handle_change, Command("change"))
        self.dispatcher.message.register(self.handle_today, Command("today"))
        self.dispatcher.message.register(self.handle_week, Command("week"))
        self.dispatcher.callback_query.register(self.handle_page, lambda c: c.data.startswith("page:"))
        self.dispatcher.callback_query.register(self.handle_subscription, lambda c: c.data.startswith("sub:"))
        self.dispatcher.callback_query.register(self.handle_unsubscribe, lambda c: c.data == "unsubscribe")

    async def handle_start(self, message: types.Message):
        chat_id = message.chat.id
        group = self.chat_subscriptions.get(chat_id)
        text = f"Привіт! Студентам групи {group}" if group else \
               "Привіт! Оберіть групу для підписки для цього чату:"
        await message.answer(text, reply_markup=None if group else self._build_keyboard(0))

    async def handle_change(self, message: types.Message):
        chat_id = message.chat.id
        active_group = self.chat_subscriptions.get(chat_id)
        await message.answer("Оберіть нову групу:", reply_markup=self._build_keyboard(0, active_group=active_group))
        logger.debug(f"Chat {chat_id} requested group change. Active: {active_group}")

    async def handle_page(self, callback: types.CallbackQuery):
        page = int(callback.data.split(":")[1])
        chat_id = callback.message.chat.id
        active_group = self.chat_subscriptions.get(chat_id)
        await callback.message.edit_reply_markup(reply_markup=self._build_keyboard(page, active_group=active_group))
        await callback.answer()

    async def handle_subscription(self, callback: types.CallbackQuery):
        chat_id, group = callback.message.chat.id, callback.data.split(":")[1]
        prev_group = self.chat_subscriptions.get(chat_id)
        self.chat_subscriptions[chat_id] = group
        await callback.message.edit_reply_markup(None)
        await callback.message.answer(f"✅ Чат підписаний на групу: {group}")
        await callback.answer()
        logger.info(f"Chat {chat_id} subscription: {prev_group} → {group}" if prev_group else f"Chat {chat_id} new subscription: {group}")
        self._schedule_today_reminders_for_group(group)

    async def handle_unsubscribe(self, callback: types.CallbackQuery):
        chat_id = callback.message.chat.id
        group = self.chat_subscriptions.pop(chat_id, None)
        if not group:
            await callback.answer()
            return

        removed_jobs = [job for job in self.scheduler.get_jobs() if job.args and chat_id in job.args[0]]
        for job in removed_jobs: self.scheduler.remove_job(job.id)
        await callback.message.edit_reply_markup(None)
        await callback.message.answer("Підписка скасована ✅")
        logger.info(f"Chat {chat_id} unsubscribed from {group}, removed {len(removed_jobs)} reminders")
        await callback.answer()

    def _format_lesson(self, lesson_number: str, lesson_data: dict) -> str | None:
        subject = lesson_data.get("Предмет")
        if not subject: return None
        start = lesson_data.get("Початок", "Не вказано")
        end = lesson_data.get("Закінчення", "Не вказано")
        teacher = lesson_data.get("Викладач", "Не вказано")
        room = lesson_data.get("Аудиторія", "Не вказано")
        return f"{lesson_number}. {start}-{end} | {subject} | {teacher} | {room}"

    def _get_today_text(self, group: str) -> str:
        weekday = ["Пн", "Вт", "Ср", "Чт", "Пт"][datetime.today().weekday()]
        lessons = self.parser.schedule.get(group, {}).get(weekday, {})
        lines = ["Розклад на сьогодні:"]
        for num, data in lessons.items():
            lesson = self._format_lesson(num, data.get("чис.", {}))
            if lesson: lines.append(lesson)
        if len(lines) == 1: lines.append("Пар немає")
        return "\n".join(lines)

    def _get_week_text(self, group: str) -> str:
        schedule = self.parser.schedule.get(group, {})
        lines = ["Розклад на тиждень:"]
        for day in ["Пн","Вт","Ср","Чт","Пт"]:
            day_lessons = schedule.get(day, {})
            day_lines = [self._format_lesson(num, l.get("чис.", {})) for num,l in day_lessons.items()]
            day_lines = [l for l in day_lines if l]
            if day_lines:
                lines.append(f"\n{day}:")
                lines.extend(day_lines)
        return "\n".join(lines)

    async def handle_today(self, message: types.Message):
        chat_id = message.chat.id
        group = self.chat_subscriptions.get(chat_id)
        if not group:
            await message.answer("Спочатку підпишіться на групу через /start або /change"); return
        await message.answer(self._get_today_text(group))

    async def handle_week(self, message: types.Message):
        chat_id = message.chat.id
        group = self.chat_subscriptions.get(chat_id)
        if not group:
            await message.answer("Спочатку підпишіться на групу через /start або /change"); return
        await message.answer(self._get_week_text(group))

    async def _send_group_lesson_reminder(self, chat_ids: list[int], lesson_number: str, lesson_data: dict):
        start = lesson_data.get("Початок", "Не вказано")
        end = lesson_data.get("Закінчення", "Не вказано")
        subject = lesson_data.get("Предмет", "Немає предмету")
        teacher = lesson_data.get("Викладач", "Не вказано")
        room = lesson_data.get("Аудиторія", "Не вказано")
        msg = f"Пара через {REMINDER_BEFORE_MINUTES} хв:\n{lesson_number}. {start}-{end} | {subject} | {teacher} | {room}"
        for chat_id in chat_ids: await self.bot.send_message(chat_id, msg)
        logger.success(f"Lesson reminder sent for {subject} to chats {chat_ids}")

    def _schedule_today_reminders_for_group(self, group: str):
        weekday_map = ["Пн", "Вт", "Ср", "Чт", "Пт"]
        today_weekday = weekday_map[datetime.today().weekday()]

        schedule = self.parser.schedule.get(group, {})
        today_schedule = schedule.get(today_weekday, {})

        now = datetime.now()
        reminders_log = []
        chat_ids = [cid for cid, g in self.chat_subscriptions.items() if g == group]

        for lesson_number, lesson_times in today_schedule.items():
            lesson_data = lesson_times.get("чис.", {})
            subject = lesson_data.get("Предмет")
            start_time_str = lesson_data.get("Початок")
            end_time_str = lesson_data.get("Закінчення", "Не вказано")

            if not subject or not start_time_str:
                continue

            hour, minute = map(int, start_time_str.split(":"))
            lesson_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            reminder_time = lesson_datetime - timedelta(minutes=REMINDER_BEFORE_MINUTES)

            if reminder_time > now:
                for cid in chat_ids:
                    self.scheduler.add_job(
                        self._send_group_lesson_reminder,
                        "date",
                        run_date=reminder_time,
                        args=[[cid], lesson_number, lesson_data]
                    )
                reminders_log.append(f"{reminder_time} - Пара {lesson_number}")

        if reminders_log:
            logger.info(f"Group {group} reminders scheduled for chats {chat_ids}: {', '.join(reminders_log)}")
        else:
            logger.info(f"No reminders today for group {group}")

    def start_scheduler(self):
        self.scheduler.add_job(self._send_today_to_all, "cron",
                               hour=TODAY_SCHEDULE_HOUR, minute=TODAY_SCHEDULE_MINUTE, day_of_week=TODAY_SCHEDULE_DAYS)
        self.scheduler.add_job(self._send_week_to_all, "cron",
                               hour=WEEK_SCHEDULE_HOUR, minute=WEEK_SCHEDULE_MINUTE, day_of_week=WEEK_SCHEDULE_DAY)
        self.scheduler.add_job(self._schedule_all_reminders, "cron",
                               hour=REMINDERS_HOUR, minute=REMINDERS_MINUTE, day_of_week=REMINDERS_DAY)

        self._schedule_all_reminders()
        self.scheduler.start()

    def _schedule_all_reminders(self):
        groups = set(self.chat_subscriptions.values())
        for group in groups:
            self._schedule_today_reminders_for_group(group)

    async def _send_today_to_all(self):
        for cid, group in self.chat_subscriptions.items():
            await self.bot.send_message(cid, self._get_today_text(group))
        logger.success("Today schedules sent to all chats")

    async def _send_week_to_all(self):
        for cid, group in self.chat_subscriptions.items():
            await self.bot.send_message(cid, self._get_week_text(group))
        logger.success("Week schedules sent to all chats")

    def save_subscriptions(self):
        try:
            with open("chat_subscriptions.json", "w", encoding="utf-8") as f:
                json.dump(self.chat_subscriptions, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.chat_subscriptions)} subscriptions")
        except Exception as e:
            logger.error(f"Failed to save subscriptions: {e}")

    def load_subscriptions(self):
        try:
            with open("chat_subscriptions.json", "r", encoding="utf-8") as f:
                self.chat_subscriptions = {int(k): v for k,v in json.load(f).items()}
            logger.info(f"Loaded {len(self.chat_subscriptions)} subscriptions")
        except Exception as e:
            logger.error(f"Failed to load subscriptions: {e}")

    async def run(self):
        try:
            self.load_subscriptions()
            self.start_scheduler()
            logger.info("Bot started successfully")
            await self.dispatcher.start_polling(self.bot)
        finally:
            self.save_subscriptions()
            logger.info("Bot stopped")
            await self.bot.session.close()
