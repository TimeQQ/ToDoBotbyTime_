import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback

import database as db
import keyboards as kb
from states import AddTask

router = Router()

# ---------- Команда /start ----------
@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот-планировщик задач.\n"
        "Используй кнопки ниже для управления.",
        reply_markup=kb.main_menu()
    )

# ---------- Отмена через инлайн-кнопку ----------
@router.callback_query(F.data == "cancel_task")
async def cancel_inline(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Действие отменено.")
    await callback.message.answer("Главное меню:", reply_markup=kb.main_menu())
    await callback.answer()

# ---------- Отмена через Reply-кнопку (если пользователь ввёл текст) ----------
@router.message(F.text == "❌ Отмена", StateFilter(AddTask))
async def cancel_reply(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=kb.main_menu())

# ---------- Добавление задачи: шаг 1 - название ----------
@router.message(F.text == "➕ Добавить задачу", StateFilter(default_state))
async def add_task_start(message: Message, state: FSMContext):
    await state.set_state(AddTask.title)
    await message.answer(
        "Введите название задачи:",
        reply_markup=kb.cancel_kb()   # reply-кнопка отмены
    )

@router.message(AddTask.title, F.text)
async def add_task_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(AddTask.date)
    # Показываем календарь
    await message.answer(
        "Выберите дату дедлайна:",
        reply_markup=await SimpleCalendar().start_calendar()
    )

# ---------- Шаг 2: выбор даты через календарь ----------
@router.callback_query(SimpleCalendarCallback.filter(), StateFilter(AddTask.date))
async def process_date(callback: CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date = await SimpleCalendar().process_selection(callback, callback_data)
    if selected:
        # Сохраняем дату в формате YYYY-MM-DD
        await state.update_data(selected_date=date.strftime("%Y-%m-%d"))
        await state.set_state(AddTask.hour)
        await callback.message.edit_text(
            f"Дата: {date.strftime('%d.%m.%Y')}\nТеперь выберите час:",
            reply_markup=kb.hours_keyboard()
        )
    else:
        await callback.message.edit_text("Выбор отменён или календарь закрыт.")
        await state.clear()
    await callback.answer()

# ---------- Шаг 3: выбор часа ----------
@router.callback_query(F.data.startswith("hour_"), StateFilter(AddTask.hour))
async def process_hour(callback: CallbackQuery, state: FSMContext):
    hour = int(callback.data.split("_")[1])
    await state.update_data(selected_hour=hour)
    await state.set_state(AddTask.minute)
    await callback.message.edit_text(
        f"Час: {hour:02d}\nТеперь выберите минуты:",
        reply_markup=kb.minutes_keyboard()
    )
    await callback.answer()

# ---------- Шаг 4: выбор минут и финальное сохранение ----------
@router.callback_query(F.data.startswith("minute_"), StateFilter(AddTask.minute))
async def process_minute(callback: CallbackQuery, state: FSMContext):
    minute = int(callback.data.split("_")[1])
    data = await state.get_data()
    title = data["title"]
    date_str = data["selected_date"]
    hour = data["selected_hour"]

    # Формируем строку дедлайна
    deadline_str = f"{date_str} {hour:02d}:{minute:02d}"

    # Сохраняем в БД
    user_id = callback.from_user.id
    db.add_task(user_id, title, deadline_str)

    await state.clear()
    await callback.message.edit_text(
        f"✅ Задача *{title}* добавлена!\nДедлайн: {deadline_str}",
        parse_mode="Markdown"
    )
    await callback.message.answer("Главное меню:", reply_markup=kb.main_menu())
    await callback.answer()

# ---------- Просмотр задач (без изменений) ----------
@router.message(F.text == "📅 Задачи на сегодня")
async def show_today_tasks(message: Message):
    tasks = db.get_tasks(message.from_user.id, only_today=True)
    if not tasks:
        await message.answer("На сегодня задач нет.")
        return
    text = "📅 *Задачи на сегодня:*\n\n"
    for task_id, title, deadline, completed in tasks:
        status = "✅" if completed else "⏳"
        text += f"{status} {task_id}. {title} (до {deadline})\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text == "📋 Все задачи")
async def show_all_tasks(message: Message):
    tasks = db.get_tasks(message.from_user.id)
    if not tasks:
        await message.answer("У вас пока нет задач.")
        return
    text = "📋 *Все задачи:*\n\n"
    for task_id, title, deadline, completed in tasks:
        status = "✅" if completed else "⏳"
        text += f"{status} {task_id}. {title} (до {deadline})\n"
    await message.answer(text, parse_mode="Markdown")

# ---------- Завершение задачи (без изменений) ----------
@router.message(F.text == "✅ Завершить задачу")
async def complete_task_prompt(message: Message):
    tasks = db.get_tasks(message.from_user.id)
    if not tasks:
        await message.answer("У вас нет задач для завершения.")
        return
    text = "Введите *номер* задачи, которую хотите отметить как выполненную:\n\n"
    for task_id, title, deadline, completed in tasks:
        status = "✅" if completed else "⏳"
        text += f"{status} {task_id}. {title} (до {deadline})\n"
    await message.answer(text, parse_mode="Markdown")

@router.message(F.text.regexp(r"^\d+$"))
async def complete_task_by_number(message: Message):
    task_id = int(message.text)
    user_id = message.from_user.id
    if db.complete_task(task_id, user_id):
        await message.answer("✅ Задача отмечена как выполненная!")
    else:
        await message.answer("❌ Задача с таким номером не найдена или вам не принадлежит.")