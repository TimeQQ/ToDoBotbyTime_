import sqlite3
from datetime import datetime

DB_NAME = "tasks.db"

def init_db():
    """Создаёт таблицу tasks, если её нет"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            deadline TEXT NOT NULL,       -- формат: YYYY-MM-DD HH:MM
            completed INTEGER DEFAULT 0,   -- 0 - не выполнено, 1 - выполнено
            notified INTEGER DEFAULT 0     -- 0 - не уведомлён, 1 - уведомлён
        )
    """)
    conn.commit()
    conn.close()

def add_task(user_id: int, title: str, deadline: str):
    """Добавляет новую задачу в БД"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (user_id, title, deadline) VALUES (?, ?, ?)",
        (user_id, title, deadline)
    )
    conn.commit()
    conn.close()

def get_tasks(user_id: int, only_today: bool = False):
    """
    Возвращает список задач пользователя.
    Если only_today=True, фильтрует по сегодняшней дате (без учёта времени).
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    if only_today:
        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute("""
            SELECT id, title, deadline, completed
            FROM tasks
            WHERE user_id = ? AND date(deadline) = ?
            ORDER BY deadline
        """, (user_id, today))
    else:
        cur.execute("""
            SELECT id, title, deadline, completed
            FROM tasks
            WHERE user_id = ?
            ORDER BY deadline
        """, (user_id,))
    tasks = cur.fetchall()
    conn.close()
    return tasks

def complete_task(task_id: int, user_id: int) -> bool:
    """Отмечает задачу как выполненную. Возвращает True, если задача принадлежит пользователю и обновлена."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET completed = 1 WHERE id = ? AND user_id = ?", (task_id, user_id))
    success = cur.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_unnotified_tasks():
    """Возвращает список задач, у которых наступил дедлайн, но уведомление ещё не отправлено."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cur.execute("""
        SELECT id, user_id, title, deadline
        FROM tasks
        WHERE deadline <= ? AND completed = 0 AND notified = 0
    """, (now,))
    tasks = cur.fetchall()
    conn.close()
    return tasks

def mark_notified(task_id: int):
    """Отмечает задачу как уведомлённую."""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("UPDATE tasks SET notified = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()