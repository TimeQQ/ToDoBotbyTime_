from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import database as db

async def check_deadlines(bot: Bot):
    """Проверяет наступившие дедлайны и отправляет напоминания"""
    tasks = db.get_unnotified_tasks()
    for task_id, user_id, title, deadline in tasks:
        try:
            await bot.send_message(
                user_id,
                f"⏰ Напоминание!\nЗадача *{title}*\nДедлайн истёк: {deadline}",
                parse_mode="Markdown"
            )
            db.mark_notified(task_id)
        except Exception as e:
            print(f"Не удалось отправить уведомление пользователю {user_id}: {e}")

def setup_scheduler(bot: Bot):
    """Настраивает и возвращает планировщик"""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_deadlines,
        trigger=IntervalTrigger(minutes=1),  # проверка каждую минуту
        kwargs={"bot": bot},
        id="deadline_checker",
        replace_existing=True
    )
    return scheduler