from aiogram.fsm.state import State, StatesGroup

class AddTask(StatesGroup):
    title = State()      # название задачи
    date = State()       # выбор даты (календарь)
    hour = State()       # выбор часа
    minute = State()     # выбор минут