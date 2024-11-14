import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import REPORT_CHANNEL_ID
from bot.create_bot import bot, dp
from bot.handlers.handlers_chat import register_handlers_chat
from bot.handlers.handlers_bot import register_handlers_bot
from db.db_queries import daily_update, get_active_users_count, get_blocked_users_count, get_muted_users_count, get_statistics, get_statistics_ban, get_statistics_mut, minute_update, monthly_update, get_statistics_new_user, get_statistics_exit_user, weekly_update


async def minute_task():
    minute_update()


async def daily_task():
    daily_update()


async def weekly_task():
    weekly_update()


async def monthly_task():
    monthly_update()


async def send_statistics():
    # Получаем статистику из базы данных
    statistics = get_statistics()
    statistics_ban = get_statistics_ban()
    statistics_mut = get_statistics_mut()
    active = get_active_users_count()
    blocked = get_blocked_users_count()
    muted = get_muted_users_count()
    statistics_new_user = get_statistics_new_user()
    statistics_exit_user = get_statistics_exit_user()
    
    # Формируем текст сообщения со статистикой
    message_text = (
        "📊 <b>Ежедневная статистика</b>\n\n"
        f"👤 <b>Активные пользователи:</b> {active}\n"
        f"🚫 <b>Заблокированные пользователи:</b> {blocked}\n"
        f"🔇 <b>Замученные пользователи:</b> {muted}\n\n"
        
        "<b>📈 Активность за последние периоды:</b>\n"
        f"• <b>1 день:</b> {statistics.one_day}\n"
        f"• <b>7 дней:</b> {statistics.seven_day}\n"
        f"• <b>30 дней:</b> {statistics.thirty_day}\n\n"
        
        "<b>👤 Новых пользователей за последние периоды:</b>\n"
        f"• <b>1 день:</b> {statistics_new_user.one_day}\n"
        f"• <b>7 дней:</b> {statistics_new_user.seven_day}\n"
        f"• <b>30 дней:</b> {statistics_new_user.thirty_day}\n\n"
        
        "<b>🔇 Вышедшех пользователей периоды:</b>\n"
        f"• <b>1 день:</b> {statistics_exit_user.one_day}\n"
        f"• <b>7 дней:</b> {statistics_exit_user.seven_day}\n"
        f"• <b>30 дней:</b> {statistics_exit_user.thirty_day}"
    )

    await bot.send_message(REPORT_CHANNEL_ID, message_text, parse_mode="HTML")


async def main() -> None:
    await bot.delete_webhook(drop_pending_updates=True)

    scheduler = AsyncIOScheduler()

    scheduler.add_job(minute_task, 'cron', minute='*')
    scheduler.add_job(send_statistics, 'cron', hour=0, minute=0)
    scheduler.add_job(daily_task, 'cron', hour=0, minute=5)
    scheduler.add_job(weekly_task, 'cron', day_of_week='mon', hour=0, minute=5)
    scheduler.add_job(monthly_task, 'cron', day=1, hour=0, minute=5)
    scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    register_handlers_bot(dp)
    register_handlers_chat(dp)
    asyncio.run(main())
