import os
import re
from markupsafe import Markup
import telebot
from flask import Flask, after_this_request, render_template, request, redirect, send_file, send_from_directory, url_for, jsonify, flash
from flask_login import LoginManager, login_user, login_required, logout_user
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

from bot.config import BOT_TOKEN, IP, REPORT_CHANNEL_ID
from db.db_queries import add_forbidden_word_db, add_user_ban, add_user_mut, delete_support_chat_by_id, delete_user_ban, delete_user_mut, get_active_users_count, get_admin_by_id, get_admin_by_username, get_all_ban_info_by_user_id, get_all_forbidden_words_db, get_all_support_chats, get_all_users, get_blocked_users_count, get_const, get_messages_by_chat, get_muted_users_count, get_statistics, get_support_chat_by_id, get_user_info, get_user_warnings, remove_forbidden_word_db, update_admin, update_const, update_statistics_ban, update_statistics_mut, update_user_status, update_user_warnings
from db.models import SupportMessage

UPLOAD_FOLDER = 'uploads'
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = "123123123"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=3)


login_manager = LoginManager(app)
login_manager.login_view = 'login'

bot = telebot.TeleBot(BOT_TOKEN)

def unmute_unblocke_user(user_id):
    update_user_status(user_id, 'Активный')


def linkify(text):
    # Шаблон для поиска URL с проверкой на переданный api_url
    url_pattern = re.compile(r'(' + re.escape(IP) + r'[^\s]*)')
    # Замена на слово "Картинка" с кликабельной ссылкой
    return Markup(url_pattern.sub(
        r'<a href="\1" class="photo-link" target="_blank">Картинка</a> <a href="\1" class="download-link" download>(Скачать)</a>', text
    ))


# Регистрация фильтра в приложении Flask
app.jinja_env.filters['linkify'] = linkify

@app.errorhandler(404)
@app.errorhandler(500)
@app.errorhandler(400)
def error_handler(e):
    return render_template('error.html', error_code=e.code), e.code

@login_manager.user_loader
def load_user(user_id):
    return get_admin_by_id(user_id)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.abspath(app.config['UPLOAD_FOLDER']), filename)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        admin = get_admin_by_username(username)
        if admin and admin.password == password:
            login_user(admin)
            return redirect(url_for('index'))
        else:
            return jsonify({'error': 'Неверные данные'}), 401

    return render_template('login.html')


@app.route('/')
@app.route('/index', methods=["POST", "GET"])
@login_required
def index():
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'desc')
    status_filter = request.args.get('status', '')

    users = get_all_users(search, status_filter)

    if sort == "asc":
        users = sorted(users, key=lambda user: datetime.strptime(
            user.last_activity, "%H:%M | %d.%m.%Y"), reverse=False)
    else:
        users = sorted(users, key=lambda user: datetime.strptime(
            user.last_activity, "%H:%M | %d.%m.%Y"), reverse=True)

    active = get_active_users_count()
    blocked = get_blocked_users_count()
    muted = get_muted_users_count()
    statistics = get_statistics()

    return render_template("index.html", users=users, active=active, blocked=blocked, muted=muted, statistics=statistics)



@app.route('/forbidden_words', methods=["POST", "GET"])
@login_required
def forbidden_words():
    forbidden_words = get_all_forbidden_words_db()
    return render_template("forbidden_words.html", forbidden_words=forbidden_words)


@app.route('/add_forbidden_word', methods=["POST", "GET"])
@login_required
def add_forbidden_word():
    word = request.form.get("word")
    add_forbidden_word_db(word)
    return redirect(url_for("forbidden_words"))


@app.route('/remove_forbidden_word/<string:word>', methods=["POST", "GET"])
@login_required
def remove_forbidden_word(word):
    remove_forbidden_word_db(word)
    return redirect(url_for("forbidden_words"))


@app.route('/user/<int:user_id>', methods=["POST", "GET"])
@login_required
def user_info(user_id):
    user = get_user_info(user_id)
    messages = get_all_ban_info_by_user_id(user_id)
    if request.method == "POST":
        if 'warnings' in request.form:
            user.warnings = int(request.form['warnings'])
            user.save()

        return redirect(url_for('user_info', user_id=user.user_id))

    return render_template("user.html", user=user, messages=messages)


@app.route('/block_user/<int:user_id>', methods=["POST"])
@login_required
def block_user(user_id):
    try:

        if request.form['block_duration']:
            block_duration = int(request.form['block_duration'])
            until_date = datetime.now() + timedelta(hours=block_duration)
            bot.kick_chat_member(get_const().chat_id, user_id, until_date=until_date)
            add_user_ban(user_id, until_date)
        else:
            bot.kick_chat_member(get_const().chat_id, user_id)
        update_user_status(user_id, 'Заблокирован')
        update_statistics_ban()
        user = get_user_info(user_id)
        bot.send_message(REPORT_CHANNEL_ID, f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={user_id}'>{user_id}</a>] #user{user_id} был заблокрован", parse_mode="HTML")
    except Exception as e:
        print(e)
    return redirect(url_for('user_info', user_id=user_id))


@app.route('/unblock_user/<int:user_id>', methods=["POST"])
@login_required
def unblock_user(user_id):
    try:
        bot.unban_chat_member(get_const().chat_id, user_id)
        bot.restrict_chat_member(get_const().chat_id, user_id, can_send_messages=True)
        update_user_status(user_id, 'Активный')
        user = get_user_info(user_id)
        bot.send_message(REPORT_CHANNEL_ID, f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={user_id}'>{user_id}</a>] #user{user_id} был разблокирован", parse_mode="HTML")
        warnings = get_user_warnings(user_id)
        update_user_warnings(user_id, -warnings)
        delete_user_ban(user_id)
        delete_user_mut(user_id)
    except Exception as e:
        print(e)
    return redirect(url_for('user_info', user_id=user_id))


@app.route('/mute_user/<int:user_id>', methods=["POST"])
@login_required
def mute_user(user_id):
    try:
        if request.form['mute_duration']:
            mute_duration = int(request.form['mute_duration'])
            until_date = datetime.now() + timedelta(hours=mute_duration)
            bot.restrict_chat_member(
                get_const().chat_id, user_id, until_date=until_date, can_send_messages=False)
            add_user_mut(user_id, until_date)
        else:
            bot.restrict_chat_member(get_const().chat_id, user_id, can_send_messages=False)
        update_user_status(user_id, 'В муте')
        update_statistics_mut()
        user = get_user_info(user_id)
        bot.send_message(REPORT_CHANNEL_ID, f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={user_id}'>{user_id}</a>] #user{user_id} был замучен", parse_mode="HTML")
    except Exception as e:
        print(e)

    return redirect(url_for('user_info', user_id=user_id))


@app.route('/unmute_user/<int:user_id>', methods=["POST"])
@login_required
def unmute_user(user_id):
    try:
        
        bot.restrict_chat_member(get_const().chat_id, user_id, can_send_messages=True)
        update_user_status(user_id, 'Активный')
        user = get_user_info(user_id)
        bot.send_message(REPORT_CHANNEL_ID, f"⚠️ Пользователь @{user.username}[<a href='tg://user?id={user_id}'>{user_id}</a>] #user{user_id} был размучен", parse_mode="HTML")
        delete_user_mut(user_id)
    except Exception as e:
        print(e)

    return redirect(url_for('user_info', user_id=user_id))
    


@app.route('/settings', methods=["POST", "GET"])
@login_required
def settings():
    const = get_const()
    if request.method == "POST":
        time_for_block = request.form.get('time_for_block', type=int)
        warnings = request.form.get('warnings', type=int)
        chat_id = request.form.get('chat_id', type=int)
        login = request.form.get('login')
        password = request.form.get('password')

        update_admin(login, password)

        if time_for_block is not None and warnings is not None:
            update_const(time_for_block, warnings, chat_id)
            return redirect(url_for('settings'))
        else:
            pass
        
    
    admin = get_admin_by_id(1)
    return render_template("settings.html", const=const, admin=admin)


@app.route('/messages_for_advertising', methods=["POST", "GET"])
@login_required
def messages_for_advertising():
    chats = get_all_support_chats()
    return render_template("messages_for_advertising.html", chats=chats)


@app.route('/chat/<int:support_id>', methods=['GET', 'POST'])
@login_required
def chat(support_id):
    chat = get_support_chat_by_id(support_id)
    if not chat:
        return redirect(url_for('messages_for_advertising'))

    if chat.status != "Отвечено":
        chat.status = 'Прочитано'
        chat.save()

    messages = get_messages_by_chat(support_id)
    return render_template('chat.html', username=chat.username, user_id=chat.user_id, messages=messages)


@app.route('/delete_support/<support_id>')
@login_required
def delete_support(support_id):
    delete_support_chat_by_id(support_id)
    return redirect(url_for('messages_for_advertising'))


@app.route('/admin_response/<support_id>', methods=['POST'])
@login_required
def admin_response(support_id):
    support_id = int(support_id)
    bot = telebot.TeleBot(BOT_TOKEN)
    chat = get_support_chat_by_id(support_id)
    if chat:
        message_text = request.form.get('message_output')
        if message_text:
            SupportMessage.create(
                support_chat=chat,
                role='admin',
                message=message_text,
                timestamp=datetime.now()
            )
            chat.status = "Отвечено"
            chat.save()
            write_to_support = telebot.types.InlineKeyboardMarkup()
            button1 = telebot.types.InlineKeyboardButton(
                text="Ответить 💬", callback_data="answer")
            write_to_support.add(button1, row_width=1)
            bot.send_message(
                chat.user_id, f"Администратор написал вам сообщение:\n\n{message_text}", reply_markup=write_to_support)
    return redirect(url_for('chat', support_id=support_id))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port='5055')
