from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


start_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Предложить рекламу 📨',
                              callback_data='start_advertising')],
    ]
)


def keyboard_not_photo():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="Нет фото", callback_data="not_photo"),

    )
    builder.adjust(1)
    return builder.as_markup()


back_to_start_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Отмена ❌',
                              callback_data='back_to_start')],
    ]
)


def mut_ban_kb(reported_user_id: int, reporter_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚫 Запретить писать нарушителю на 1 час",
                    callback_data=f"mute_user_{reported_user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🚫 Запретить писать репортеру на 1 час",
                    callback_data=f"mute_reporter_{reporter_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ Заблокировать нарушителя",
                    callback_data=f"ban_user_{reported_user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⛔ Заблокировать репортера",
                    callback_data=f"ban_reporter_{reporter_id}"
                )
            ],
        ]
    )


def ban_unmut_kb(reported_user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⛔ Заблокировать нарушителя",
                    callback_data=f"ban_user_{reported_user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔊 Размутить нарушителя",
                    callback_data=f"unmut_user_{reported_user_id}"
                )
            ],
        ]
    )
