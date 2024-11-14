from datetime import datetime
from uuid import uuid4
from aiogram import Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.config import IP
from bot.create_bot import StateForm, bot
from bot.keyboards.user_keyboards import keyboard_not_photo, start_kb, back_to_start_kb
from db.db_queries import create_support_message, handle_support_message


async def start_bot(message: Message, state: FSMContext):
    await state.clear()
    await bot.send_message(message.from_user.id, "Добро пожаловать👋\n\nЗдесь вы можете предложить свою рекламу!\nДля этого нажмите кнопку ниже👇🏻", reply_markup=start_kb)


async def start_advertising(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await callback_query.message.answer("Пожалуйста, отправьте текст.")
    await state.set_state(StateForm.advertising_text)

async def image_advertising(message: Message, state: FSMContext):
    await state.update_data(advertising_text=message.text)
    await message.answer("Теперь отправьте фото", reply_markup=keyboard_not_photo())
    await state.set_state(StateForm.advertising_image)


async def not_photo(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    data = await state.get_data()
    advertising_text = data['advertising_text']
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or callback_query.from_user.first_name

    chat, created = handle_support_message(user_id, username, advertising_text)

    if not created:
        chat.last_message_time = datetime.now()
        chat.status = 'Не прочитано'
        chat.subject = advertising_text[:10] + \
            ('...' if len(advertising_text) > 10 else '')
        chat.save()
    create_support_message(chat=chat,
                           role='user',
                           message_text=advertising_text,
                           )
    await callback_query.message.answer("Ваше обращение отправлено!")
    await state.clear()

async def finish_advertising(message: Message, state: FSMContext):
    name = f'uploads/{uuid4()}.jpeg'
    await message.bot.download(file=message.photo[-1].file_id, destination=name)
    data = await state.get_data()
    advertising_text = data['advertising_text']
    text = f"{advertising_text}\n\n{IP}{name}"
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    chat, created = handle_support_message(user_id, username, text)

    if not created:
        chat.last_message_time = datetime.now()
        chat.status = 'Не прочитано'
        chat.subject = text[:10] + \
            ('...' if len(text) > 10 else '')
        chat.save()
    create_support_message(chat=chat,
                           role='user',
                           message_text=text,
                           )
    await message.answer("Ваше обращение отправлено!")
    await state.clear()

async def answer(callback_query: CallbackQuery, state: FSMContext):
    await state.set_state(StateForm.answer)
    await callback_query.message.answer("Введите ответ", reply_markup=back_to_start_kb)
    
async def answer_text(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    chat, created = handle_support_message(user_id, username, message.text)

    if not created:
        chat.last_message_time = datetime.now()
        chat.status = 'Не прочитано'
        chat.subject = message.text[:10] + \
            ('...' if len(message.text) > 10 else '')
        chat.save()
    create_support_message(chat=chat,
                           role='user',
                           message_text=message.text,
                           )
    await state.clear()
    await message.answer("Ваше сообщение отправлено администратору!")

def register_handlers_bot(dp: Dispatcher):
    dp.message.register(start_bot, lambda message: message.text == '/start' and message.chat.type == 'private')
    dp.callback_query.register(start_advertising, lambda callback_query: callback_query.data == 'start_advertising' and callback_query.message.chat.type == 'private')
    dp.message.register(image_advertising, lambda message: message.text and message.chat.type == 'private', StateForm.advertising_text)
    dp.callback_query.register(not_photo, lambda callback_query: callback_query.data == 'not_photo' and callback_query.message.chat.type == 'private', StateForm.advertising_image)
    dp.message.register(finish_advertising, lambda message: message.photo and message.chat.type == 'private', StateForm.advertising_image)
    dp.callback_query.register(answer, lambda callback_query: callback_query.data == 'answer' and callback_query.message.chat.type == 'private')
    dp.message.register(answer_text, lambda message: message.text and message.chat.type == 'private', StateForm.answer)
    dp.callback_query.register(start_bot, lambda callback_query: callback_query.data == 'back_to_start' and callback_query.message.chat.type == 'private')