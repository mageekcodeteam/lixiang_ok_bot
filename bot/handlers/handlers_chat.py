import pytz

from datetime import datetime, timedelta
from collections import defaultdict
from aiogram import Bot, Dispatcher
from aiogram.types import Message, ChatPermissions, CallbackQuery
from aiogram.filters import Command, CommandObject
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER
from aiogram.filters import CommandStart, ChatMemberUpdatedFilter

from bot.config import REPORT_CHANNEL_ID
from bot.create_bot import bot
from bot.keyboards.user_keyboards import ban_unmut_kb, mut_ban_kb
from db.db_queries import add_ban_info, add_user_ban, add_user_mut, create_user_info_db, get_all_forbidden_words_db, get_const, get_user_info, get_user_info_by_username, get_user_warnings, update_statistics, update_statistics_ban, update_statistics_exit_user, update_statistics_mut, update_statistics_new_user, update_user_info_db, update_user_status, update_user_warnings, user_check_mut

# Для хранения сообщений пользователей
user_messages = defaultdict(list)

# Ограничение на количество сообщений за определенное время
MESSAGE_LIMIT = 3  # Количество сообщений
TIME_WINDOW = timedelta(seconds=3)  # Время для ограничения


async def handle_new_member(message: Message):
    create_user_info_db(message.from_user.id, message.from_user.username)
    update_statistics_new_user()


async def handle_exit_member(message: Message):
    update_statistics_exit_user()


async def check_message(message: Message):
    forbidden_words = get_all_forbidden_words_db()
    prohibited_words = {fw.word.lower() for fw in forbidden_words}
    update_user_info_db(message.from_user.id, message.from_user.username)
    update_statistics()

    current_time = datetime.now()
    user_id = message.from_user.id
    user_messages[user_id].append(current_time)

    user_messages[user_id] = [msg_time for msg_time in user_messages[user_id]
                              if current_time - msg_time <= TIME_WINDOW]

    if len(user_messages[user_id]) > MESSAGE_LIMIT:
        until_date = datetime.now() + timedelta(minutes=2)
        permissions = ChatPermissions(can_send_messages=False)

        await bot.restrict_chat_member(
            int(get_const().chat_id), user_id, permissions=permissions, until_date=until_date
        )

        if not user_check_mut(user_id):
            add_user_mut(user_id, until_date)
            update_user_status(user_id, 'В муте')
            moscow_tz = pytz.timezone('Europe/Moscow')
            now_moscow = datetime.now(moscow_tz)

            formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')
            await bot.send_message(REPORT_CHANNEL_ID, f"⚠️ Пользователь @{message.from_user.username}[<a href='tg://user?id={user_id}'>{user_id}</a>] #user{user_id} был замучен\nВремя: {formatted_date}\nПричина: <code>Спам</code>", parse_mode="HTML")
        await message.delete()
        return

    message_text = message.text.lower() if message.text else ''
    caption_text = message.caption.lower() if message.caption else ''

    if prohibited_words and (any(word in message_text for word in prohibited_words) or any(word in caption_text for word in prohibited_words)):
        await message.delete()
        update_user_warnings(message.from_user.id)
        warnings = get_user_warnings(message.from_user.id)
        const = get_const()
        hours = const.time_for_block
        lim_warnings = const.warnings
        if hours != 0:
            until_date = datetime.now() + timedelta(hours=hours)
        else:
            until_date = None
        if message_text:
            add_ban_info(message.from_user.id, message_text)
        else:
            add_ban_info(message.from_user.id, caption_text)
        if warnings < lim_warnings:
            pass
            # await message.answer(f"Пользователь <a href='https://t.me/{message.from_user.username}'>{message.from_user.first_name}</a> (@{message.from_user.username}) использовал запретное слово!\n\nУ него осталось {lim_warnings - warnings}/{lim_warnings} предупреждений", parse_mode="HTML", disable_web_page_preview=True)
        else:
            pass
            # await message.answer(f"Пользователь <a href='https://t.me/{message.from_user.username}'>{message.from_user.first_name}</a> (@{message.from_user.username}) использовал запретное слово и был забанен!", parse_mode="HTML", disable_web_page_preview=True)
            # await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id, until_date=until_date)
            # update_user_status(message.from_user.id, "Заблокирован")
            await bot.restrict_chat_member(
                int(get_const().chat_id), user_id, permissions=ChatPermissions(can_send_messages=False)
            )
            update_user_status(user_id, "В муте")
            update_statistics_mut()
            moscow_tz = pytz.timezone('Europe/Moscow')
            now_moscow = datetime.now(moscow_tz)

            formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')
            await bot.send_message(
                REPORT_CHANNEL_ID,
                f"⚠️ Пользователь @{message.from_user.username}[<a href='tg://user?id={message.from_user.id}'>{message.from_user.id}</a>] #user{message.from_user.id} был замучен\n"
                f"Время: {formatted_date}\n"
                f"Сообщение:\n\n<code>{message_text or caption_text}</code>",
                parse_mode="HTML", reply_markup=ban_unmut_kb(message.from_user.id)
            )


async def report_command(message: Message):
    await message.delete()
    if message.reply_to_message:
        reported_user = message.reply_to_message.from_user
        reported_message_text = message.reply_to_message.text or message.reply_to_message.caption or "Сообщение без текста"

        if len(reported_message_text) > 4000:
            reported_message_text = reported_message_text[:4000] + \
                "... [текст сокращен]"

        chat_id_str = str(abs(int(get_const().chat_id)))[3:]
        message_link = f"https://t.me/c/{chat_id_str}/{message.reply_to_message.message_id}"

        moscow_tz = pytz.timezone('Europe/Moscow')
        now_moscow = datetime.now(moscow_tz)

        formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')

        report_text = (
            f"🆘 Поступила жалоба в группе!\n\n"
            f"Пользователь <a href='tg://user?id={message.from_user.id}'>{message.from_user.full_name}</a> [@{message.from_user.username}][{message.from_user.id}] #user{message.from_user.id} "
            f"пожаловался на <a href='tg://user?id={reported_user.id}'>{reported_user.full_name}</a> [@{reported_user.username}][{reported_user.id}] #user{reported_user.id}\n"
            f"Время: {formatted_date}\n"
            f"Сообщение:\n\n<code>{reported_message_text}</code>\n\n"
            f"<a href='{message_link}'>Перейти к сообщению</a>"
        )

        await bot.send_message(REPORT_CHANNEL_ID, report_text, reply_markup=mut_ban_kb(reported_user.id, message.from_user.id), parse_mode="HTML")


async def button_handler(callback_query: CallbackQuery):
    user_id = callback_query.data.split('_')[2]
    action = '_'.join(callback_query.data.split('_')[:2])
    action_text = ""

    if action == 'mute_user':
        until_date = datetime.now() + timedelta(hours=1)
        await bot.restrict_chat_member(
            int(get_const().chat_id), user_id, permissions=ChatPermissions(can_send_messages=False), until_date=until_date
        )
        add_user_mut(user_id, until_date)
        update_user_status(user_id, "В муте")
        update_statistics_mut()
        action_text = "Нарушителю запрещено писать на 1 час."
    elif action == 'mute_reporter':
        until_date = datetime.now() + timedelta(hours=1)
        await bot.restrict_chat_member(
            int(get_const().chat_id), user_id, permissions=ChatPermissions(can_send_messages=False), until_date=until_date
        )
        add_user_mut(user_id, until_date)
        update_user_status(user_id, "В муте")
        update_statistics_mut()
        action_text = "Отправителю запрещено писать на 1 час."
    elif action == 'ban_user':
        await bot.ban_chat_member(chat_id=int(get_const().chat_id), user_id=user_id)
        update_user_status(user_id, "Заблокирован")
        update_statistics_ban()
        action_text = "Нарушитель забанен."
    elif action == 'ban_reporter':
        await bot.ban_chat_member(chat_id=int(get_const().chat_id), user_id=user_id)
        update_user_status(user_id, "Заблокирован")
        update_statistics_ban()
        action_text = "Отправитель забанен."
    elif action == 'unmut_user':
        await bot.restrict_chat_member(int(get_const().chat_id), user_id, permissions=ChatPermissions(can_send_messages=True))
        update_user_status(user_id, 'Активный')
        action_text = "Пользователь размучен."

    await bot.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        text=f"{callback_query.message.text}\n\n{action_text}"
    )


async def ban_command(message: Message):
    await message.delete()
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if message.reply_to_message and (chat_member.status == "creator" or chat_member.status == "administrator"):
        reported_user = message.reply_to_message.from_user
        initiator = message.from_user  # Кто инициировал команду
        # Сообщение пользователя
        reported_message = message.reply_to_message.text or message.reply_to_message.caption

        if len(message.text.split()) == 2:
            time = int(message.text.split()[1])
            until_date = datetime.now() + timedelta(hours=time)
            add_user_ban(reported_user.id, until_date)
        else:
            until_date = None
        await bot.ban_chat_member(chat_id=int(get_const().chat_id), user_id=reported_user.id, until_date=until_date)

        update_user_status(reported_user.id, "Заблокирован")
        update_statistics_ban()
        moscow_tz = pytz.timezone('Europe/Moscow')
        now_moscow = datetime.now(moscow_tz)

        formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')

        await bot.send_message(
            REPORT_CHANNEL_ID,
            f"⚠️ Пользователь @{reported_user.username}[<a href='tg://user?id={reported_user.id}'>{reported_user.id}</a>] #user{reported_user.id} был заблокирован\n"
            f"Забанен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
            f"Время: {formatted_date}\n"
            f"Сообщение:\n\n<code>{reported_message}</code>",
            parse_mode="HTML"
        )
    elif (chat_member.status == "creator" or chat_member.status == "administrator"):
        m_data = message.text.split()

        if len(m_data) != 2:
            await message.answer("⚠️ Команда должна иметь вид /ban @username или ID")
        else:
            if m_data[1].isdigit():
                reported_user = get_user_info(m_data[1])
                initiator = message.from_user  # Кто инициировал команду

                await bot.ban_chat_member(chat_id=int(get_const().chat_id), user_id=reported_user.id)

                update_user_status(reported_user.id, "Заблокирован")
                update_statistics_ban()
                moscow_tz = pytz.timezone('Europe/Moscow')
                now_moscow = datetime.now(moscow_tz)

                formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')
                await bot.send_message(
                    REPORT_CHANNEL_ID,
                    f"⚠️ Пользователь @{reported_user.username}[<a href='tg://user?id={reported_user.id}'>{reported_user.id}</a>] #user{reported_user.id} был заблокирован\n"
                    f"Забанен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
                    f"Время: {formatted_date}\n",
                    parse_mode="HTML"
                )

            else:
                user_id = get_user_info_by_username(
                    m_data[1].replace('@', '')).user_id
                reported_user = get_user_info(user_id)
                initiator = message.from_user  # Кто инициировал команду

                await bot.ban_chat_member(chat_id=int(get_const().chat_id), user_id=reported_user.user_id)

                update_user_status(reported_user.user_id, "Заблокирован")
                update_statistics_ban()
                moscow_tz = pytz.timezone('Europe/Moscow')
                now_moscow = datetime.now(moscow_tz)

                formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')
                await bot.send_message(
                    REPORT_CHANNEL_ID,
                    f"⚠️ Пользователь @{reported_user.username}[<a href='tg://user?id={reported_user.user_id}'>{reported_user.user_id}</a>] #user{reported_user.user_id} был заблокирован\n"
                    f"Забанен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
                    f"Время: {formatted_date}\n",
                    parse_mode="HTML"
                )


async def mut_command(message: Message):
    await message.delete()
    chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if message.reply_to_message and (chat_member.status == "creator" or chat_member.status == "administrator"):
        reported_user = message.reply_to_message.from_user
        initiator = message.from_user  # Кто инициировал команду
        # Сообщение пользователя
        reported_message = message.reply_to_message.text or message.reply_to_message.caption

        if len(message.text.split()) == 2:
            time = int(message.text.split()[1])
            until_date = datetime.now() + timedelta(hours=time)
            add_user_mut(reported_user.id, until_date)
        else:
            until_date = None
        await bot.restrict_chat_member(
            int(get_const().chat_id), reported_user.id, permissions=ChatPermissions(can_send_messages=False), until_date=until_date
        )

        update_user_status(reported_user.id, "В муте")
        update_statistics_mut()
        moscow_tz = pytz.timezone('Europe/Moscow')
        now_moscow = datetime.now(moscow_tz)

        formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')
        await bot.send_message(
            REPORT_CHANNEL_ID,
            f"⚠️ Пользователь @{reported_user.username}[<a href='tg://user?id={reported_user.id}'>{reported_user.id}</a>] #user{reported_user.id} был замучен\n"
            f"Замучен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
            f"Время: {formatted_date}\n"
            f"Сообщение:\n\n<code>{reported_message}</code>",
            parse_mode="HTML"
        )
    elif (chat_member.status == "creator" or chat_member.status == "administrator"):
        m_data = message.text.split()

        if len(m_data) != 2:
            await message.answer("⚠️ Команда должна иметь вид /mute @username или ID")
        else:
            if m_data[1].isdigit():
                reported_user = get_user_info(m_data[1])
                initiator = message.from_user  # Кто инициировал команду
                await bot.restrict_chat_member(
                    int(get_const().chat_id), reported_user.id, permissions=ChatPermissions(can_send_messages=False)
                )

                update_user_status(reported_user.id, "В муте")
                update_statistics_mut()
                moscow_tz = pytz.timezone('Europe/Moscow')
                now_moscow = datetime.now(moscow_tz)

                formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')
                await bot.send_message(
                    REPORT_CHANNEL_ID,
                    f"⚠️ Пользователь @{reported_user.username}[<a href='tg://user?id={reported_user.id}'>{reported_user.id}</a>] #user{reported_user.id} был замучен\n"
                    f"Замучен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
                    f"Время: {formatted_date}\n",
                    parse_mode="HTML"
                )
            else:
                user_id = get_user_info_by_username(
                    m_data[1].replace('@', '')).user_id
                reported_user = get_user_info(user_id)
                initiator = message.from_user  # Кто инициировал команду
                print(reported_user.id)
                await bot.restrict_chat_member(
                    int(get_const().chat_id), reported_user.user_id, permissions=ChatPermissions(can_send_messages=False)
                )

                update_user_status(reported_user.user_id, "В муте")
                update_statistics_mut()
                moscow_tz = pytz.timezone('Europe/Moscow')
                now_moscow = datetime.now(moscow_tz)

                formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')
                await bot.send_message(
                    REPORT_CHANNEL_ID,
                    f"⚠️ Пользователь @{reported_user.username}[<a href='tg://user?id={reported_user.user_id}'>{reported_user.user_id}</a>] #user{reported_user.user_id} был замучен\n"
                    f"Замучен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
                    f"Время: {formatted_date}\n",
                    parse_mode="HTML"
                )


async def unban_command(message: Message):
    await message.delete()
    initiator = message.from_user  # Кто инициировал команду
    m_data = message.text.split()

    if len(m_data) != 2:
        await message.answer("⚠️ Команда должна иметь вид /unban @username или ID")
    else:
        moscow_tz = pytz.timezone('Europe/Moscow')
        now_moscow = datetime.now(moscow_tz)
        formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')

        if m_data[1].isdigit():
            user_id = int(m_data[1])
            await bot.unban_chat_member(int(get_const().chat_id), user_id)
            update_user_status(user_id, 'Активный')
            user = get_user_info(user_id)
            await bot.send_message(
                REPORT_CHANNEL_ID,
                f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={user_id}'>{user_id}</a>] #user{user_id} был разблокирован\n"
                f"Разбанен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
                f"Время: {formatted_date}",
                parse_mode="HTML"
            )
        else:
            user_id = get_user_info_by_username(
                m_data[1].replace('@', '')).user_id
            await bot.unban_chat_member(int(get_const().chat_id), user_id)
            update_user_status(user_id, 'Активный')
            user = get_user_info(user_id)
            await bot.send_message(
                REPORT_CHANNEL_ID,
                f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={user_id}'>{user_id}</a>] #user{user_id} был разблокирован\n"
                f"Разбанен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
                f"Время: {formatted_date}",
                parse_mode="HTML"
            )


async def unmut_command(message: Message):
    await message.delete()
    initiator = message.from_user  # Кто инициировал команду
    m_data = message.text.split()

    if len(m_data) != 2:
        await message.answer("⚠️ Команда должна иметь вид /unmute @username или ID")
    else:
        moscow_tz = pytz.timezone('Europe/Moscow')
        now_moscow = datetime.now(moscow_tz)
        formatted_date = now_moscow.strftime('%d.%m.%Y %H:%M')

        if m_data[1].isdigit():
            user_id = int(m_data[1])
            await bot.restrict_chat_member(int(get_const().chat_id), user_id, permissions=ChatPermissions(can_send_messages=True))
            update_user_status(user_id, 'Активный')
            user = get_user_info(user_id)
            await bot.send_message(
                REPORT_CHANNEL_ID,
                f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={user_id}'>{user_id}</a>] #user{user_id} был размучен\n"
                f"Размучен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
                f"Время: {formatted_date}",
                parse_mode="HTML"
            )
        else:
            user_id = get_user_info_by_username(
                m_data[1].replace('@', '')).user_id
            await bot.restrict_chat_member(int(get_const().chat_id), user_id, permissions=ChatPermissions(can_send_messages=True))
            update_user_status(user_id, 'Активный')
            user = get_user_info(user_id)
            await bot.send_message(
                REPORT_CHANNEL_ID,
                f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={user_id}'>{user_id}</a>] #user{user_id} был размучен\n"
                f"Размучен по команде от @{initiator.username}[<a href='tg://user?id={initiator.id}'>{initiator.id}</a>] #user{initiator.id}\n"
                f"Время: {formatted_date}",
                parse_mode="HTML"
            )


def register_handlers_chat(dp: Dispatcher):
    dp.chat_member.register(
        handle_new_member, ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER)
    )
    dp.chat_member.register(
        handle_exit_member, ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER)
    )
    dp.message.register(report_command, lambda message: message.text ==
                        '/report' and message.chat.id == int(get_const().chat_id))

    dp.message.register(ban_command, lambda message: message.text and message.text.startswith(
        '/ban') and (message.chat.id == int(get_const().chat_id) or REPORT_CHANNEL_ID))
    dp.message.register(mut_command, lambda message: message.text and message.text.startswith(
        '/mut') and (message.chat.id == int(get_const().chat_id) or REPORT_CHANNEL_ID))

    dp.message.register(unban_command, lambda message: message.text and message.text.startswith(
        '/unban') and (message.chat.id == int(get_const().chat_id) or REPORT_CHANNEL_ID))
    dp.message.register(unmut_command, lambda message: message.text and message.text.startswith(
        '/unmut') and (message.chat.id == int(get_const().chat_id) or REPORT_CHANNEL_ID))

    dp.message.register(
        check_message, lambda message: message.text or message.caption and message.chat.id == int(get_const().chat_id))
    dp.callback_query.register(button_handler)
