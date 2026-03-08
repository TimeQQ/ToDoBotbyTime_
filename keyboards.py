from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ----- Reply-клавиатуры (обычные кнопки под полем ввода) -----

def main_menu() -> ReplyKeyboardMarkup:
    """Главное меню с основными действиями"""
    kb = [
        [KeyboardButton(text="➕ Добавить задачу")],
        [KeyboardButton(text="📅 Задачи на сегодня")],
        [KeyboardButton(text="📋 Все задачи")],
        [KeyboardButton(text="✅ Завершить задачу")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def cancel_kb() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены (используется во время FSM)"""
    kb = [[KeyboardButton(text="❌ Отмена")]]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# ----- Inline-клавиатуры (кнопки под сообщением) -----

def cancel_inline_kb() -> InlineKeyboardMarkup:
    """Инлайн-кнопка отмены"""
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Отмена", callback_data="cancel_task")
    return builder.as_markup()

def hours_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора часа (0-23)"""
    builder = InlineKeyboardBuilder()
    # Часы с 0 до 23, по 6 в ряд
    for h in range(0, 24):
        builder.button(text=f"{h:02d}", callback_data=f"hour_{h}")
    builder.button(text="❌ Отмена", callback_data="cancel_task")
    builder.adjust(6)  # по 6 кнопок в ряду
    return builder.as_markup()

def minutes_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора минут с шагом 15 (00,15,30,45)"""
    builder = InlineKeyboardBuilder()
    for m in [0, 15, 30, 45]:
        builder.button(text=f"{m:02d}", callback_data=f"minute_{m}")
    builder.button(text="❌ Отмена", callback_data="cancel_task")
    builder.adjust(4)  # по 4 кнопки в ряду
    return builder.as_markup()