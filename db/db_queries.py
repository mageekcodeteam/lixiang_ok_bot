from bot.config import BOT_TOKEN, REPORT_CHANNEL_ID
from db.models import Admin, BanInfo, Const, Forbidden_words, Statistics, Statistics_ban, Statistics_exit_user, Statistics_mut, Statistics_new_user, SupportChat, SupportMessage, User, UserBanInfo, UserMutInfo
from datetime import datetime

import telebot

bot = telebot.TeleBot(BOT_TOKEN)


def add_forbidden_word_db(word: str) -> None:
    check = Forbidden_words.get_or_none(Forbidden_words.word == word)
    if not check:
        Forbidden_words.create(word=word)


def remove_forbidden_word_db(word: str) -> None:
    word_to_delete = Forbidden_words.get_or_none(Forbidden_words.word == word)
    if word_to_delete is not None:
        word_to_delete.delete_instance()


def get_all_forbidden_words_db():
    forbidden_words = Forbidden_words.select()
    return forbidden_words

def create_user_info_db(user_id, username) -> None:
    user = User.get_or_none(User.user_id == user_id)
    if not user:
        if not username:
            username = "Отсутсвует"
        User.create(
            user_id=user_id,
            username=username,
            number_of_messages=0,
            status="Активный",
            last_activity=datetime.now().strftime("%H:%M | %d.%m.%Y"),
            warnings=0
        )

def update_user_info_db(user_id, username) -> None:
    user = User.get_or_none(User.user_id == user_id)
    if not user:
        if not username:
            username = "Отсутсвует"
        User.create(
            user_id=user_id,
            username=username,
            number_of_messages=1,
            status="Активный",
            last_activity=datetime.now().strftime("%H:%M | %d.%m.%Y"),
            warnings=0
        )
    else:
        if not username:
            username = "Отсутсвует"
        user.user_id = user_id
        user.username = username
        user.number_of_messages += 1
        user.status = "Активный"
        user.last_activity = datetime.now().strftime("%H:%M | %d.%m.%Y")
        user.save()


def update_user_warnings(user_id, warnings=1) -> None:
    user = User.get_or_none(User.user_id == user_id)
    user.warnings += warnings
    user.save()


def update_user_status(user_id, status) -> None:
    user = User.get_or_none(User.user_id == user_id)
    user.status = status
    user.save()


def get_user_warnings(user_id):
    user = User.get_or_none(User.user_id == user_id)
    return user.warnings


def get_all_users(search=None, status=None):
    query = User.select()

    if search:
        query = query.where(
            (User.username.ilike(f'%{search}%')) |
            (User.last_activity.ilike(f'%{search}%')) |
            (User.user_id.ilike(f'%{search}%'))
        )

    if status:
        query = query.where(User.status == status)

    return query


def get_user_info(user_id):
    user = User.get_or_none(User.user_id == user_id)
    return user


def get_user_info_by_username(username):
    user = User.get_or_none(User.username == username)
    return user


def get_active_users_count():
    return User.select().where(User.status == "Активный").count()


def get_muted_users_count():
    return User.select().where(User.status == "В муте").count()


def get_blocked_users_count():
    return User.select().where(User.status == "Заблокирован").count()


def minute_update():
    current_time = datetime.now().replace(second=0, microsecond=0)
    for ban in UserBanInfo.select():
        if ban.timestamp.replace(second=0, microsecond=0) <= current_time:
            update_user_status(ban.user_id, 'Активный')
            user = get_user_info(ban.user_id)
            bot.send_message(
                REPORT_CHANNEL_ID, f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={ban.user_id}'>{ban.user_id}</a>] #user{ban.user_id} был разблокирован", parse_mode="HTML")
            bot.unban_chat_member(get_const().chat_id, ban.user_id)
            warnings = get_user_warnings(ban.user_id)
            update_user_warnings(ban.user_id, -warnings)
            delete_user_ban(ban.user_id)

    for mute in UserMutInfo.select():
        if mute.timestamp.replace(second=0, microsecond=0) <= current_time:
            update_user_status(mute.user_id, 'Активный')
            user = get_user_info(mute.user_id)
            bot.send_message(
                REPORT_CHANNEL_ID, f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={mute.user_id}'>{mute.user_id}</a>] #user{mute.user_id} был размучен", parse_mode="HTML")
            delete_user_mut(mute.user_id)


def daily_update():
    statistics, created = Statistics.get_or_create(id=1)
    statistics.one_day = 0
    statistics.save()
    statistics, created = Statistics_ban.get_or_create(id=1)
    statistics.one_day = 0
    statistics.save()
    statistics, created = Statistics_mut.get_or_create(id=1)
    statistics.one_day = 0
    statistics.save()
    statistics, created = Statistics_new_user.get_or_create(id=1)
    statistics.one_day = 0
    statistics.save()
    statistics, created = Statistics_exit_user.get_or_create(id=1)
    statistics.one_day = 0
    statistics.save()


def weekly_update():
    statistics, created = Statistics.get_or_create(id=1)
    statistics.seven_day = 0
    statistics.save()
    statistics, created = Statistics_ban.get_or_create(id=1)
    statistics.seven_day = 0
    statistics.save()
    statistics, created = Statistics_mut.get_or_create(id=1)
    statistics.seven_day = 0
    statistics.save()
    statistics, created = Statistics_new_user.get_or_create(id=1)
    statistics.seven_day = 0
    statistics.save()
    statistics, created = Statistics_exit_user.get_or_create(id=1)
    statistics.seven_day = 0
    statistics.save()


def monthly_update():
    statistics, created = Statistics.get_or_create(id=1)
    statistics.thirty_day = 0
    statistics.save()
    statistics, created = Statistics_ban.get_or_create(id=1)
    statistics.thirty_day = 0
    statistics.save()
    statistics, created = Statistics_mut.get_or_create(id=1)
    statistics.thirty_day = 0
    statistics.save()
    statistics, created = Statistics_new_user.get_or_create(id=1)
    statistics.thirty_day = 0
    statistics.save()
    statistics, created = Statistics_exit_user.get_or_create(id=1)
    statistics.thirty_day = 0
    statistics.save()


def get_statistics():
    statistics, created = Statistics.get_or_create(id=1)
    return statistics

def get_statistics_ban():
    statistics, created = Statistics_ban.get_or_create(id=1)
    return statistics

def get_statistics_mut():
    statistics, created = Statistics_mut.get_or_create(id=1)
    return statistics

def get_statistics_new_user():
    statistics, created = Statistics_new_user.get_or_create(id=1)
    return statistics

def get_statistics_exit_user():
    statistics, created = Statistics_exit_user.get_or_create(id=1)
    return statistics

def update_statistics():
    statistics, created = Statistics.get_or_create(id=1)
    statistics.one_day += 1
    statistics.seven_day += 1
    statistics.thirty_day += 1
    statistics.save()

def update_statistics_ban():
    statistics, created = Statistics_ban.get_or_create(id=1)
    statistics.one_day += 1
    statistics.seven_day += 1
    statistics.thirty_day += 1
    statistics.save()

def update_statistics_mut():
    statistics, created = Statistics_mut.get_or_create(id=1)
    statistics.one_day += 1
    statistics.seven_day += 1
    statistics.thirty_day += 1
    statistics.save()

def update_statistics_new_user():
    statistics, created = Statistics_new_user.get_or_create(id=1)
    statistics.one_day += 1
    statistics.seven_day += 1
    statistics.thirty_day += 1
    statistics.save()

def update_statistics_exit_user():
    statistics, created = Statistics_exit_user.get_or_create(id=1)
    statistics.one_day += 1
    statistics.seven_day += 1
    statistics.thirty_day += 1
    statistics.save()


def get_const():
    const, created = Const.get_or_create(id=1)
    return const


def update_const(time_for_block, warnings, chat_id):
    const, created = Const.get_or_create(id=1)
    const.time_for_block = time_for_block
    const.warnings = warnings
    const.chat_id = chat_id
    const.save()


def get_all_support_chats():
    """
    Получить все чаты поддержки, отсортированные по времени последнего сообщения.
    """
    return SupportChat.select().order_by(SupportChat.last_message_time.desc())


def get_support_chat_by_id(support_id):
    """
    Получить чат поддержки по ID.
    """
    return SupportChat.get_or_none(SupportChat.id == support_id)


def delete_support_chat_by_id(support_id):
    """
    Удалить чат поддержки по ID.
    """
    try:
        chat = SupportChat.get_or_none(SupportChat.id == support_id)
        chat.delete_instance(recursive=True)
    except SupportChat.DoesNotExist:
        return {'status': 'error'}


def get_messages_by_chat(chat_id):
    """
    Получить сообщения по чату поддержки.
    """
    chat = get_support_chat_by_id(chat_id)
    if not chat:
        return []
    return SupportMessage.select().where(SupportMessage.support_chat == chat).order_by(SupportMessage.timestamp)


def create_support_message(chat, role, message_text):
    """
    Создать сообщение в чате поддержки.
    """
    return SupportMessage.create(
        support_chat=chat,
        role=role,
        message=message_text,
        timestamp=datetime.now()
    )


def handle_support_message(user_id: str, username: str, message_text: str):
    """
    Обработать сообщение пользователя и создать/обновить чат поддержки.
    """
    chat, created = SupportChat.get_or_create(
        user_id=user_id,
        defaults={
            'username': username,
            'subject': message_text[:10] + ('...' if len(message_text) > 10 else ''),
            'last_message_time': datetime.now(),
            'status': 'Не прочитано'
        }
    )

    if not created:
        chat.last_message_time = datetime.now()
        chat.status = 'Не прочитано'
        chat.subject = message_text[:10] + \
            ('...' if len(message_text) > 10 else '')
        chat.save()

    return chat, created


def add_user_ban(user_id, time):
    UserBanInfo.create(
        user_id=user_id,
        timestamp=time,
    )


def add_user_mut(user_id, time):
    UserMutInfo.create(
        user_id=user_id,
        timestamp=time,
    )


def delete_user_ban(user_id):
    try:
        query = UserBanInfo.delete().where(UserBanInfo.user_id == user_id)
        query.execute()
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def delete_user_mut(user_id):
    try:
        query = UserMutInfo.delete().where(UserMutInfo.user_id == user_id)
        query.execute()
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def get_admin_by_username(username):
    user = Admin.get_or_none(Admin.username == username)
    return user


def get_admin_by_id(id):
    user = Admin.get_or_none(Admin.id == id)
    return user


def add_ban_info(user_id, message):
    user = BanInfo.create(user_id=user_id, message=message)
    return user


def get_all_ban_info_by_user_id(user_id):
    messages = BanInfo.select().where(BanInfo.user_id == user_id)
    return messages


def user_check_mut(user_id):
    user = UserMutInfo.get_or_none(UserMutInfo.user_id == user_id)
    return user


def update_admin(username, password):
    user = Admin.get_or_none(Admin.id == 1)
    user.username = username
    user.password = password
    user.save()
