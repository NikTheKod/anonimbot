import aiosqlite
from typing import Optional

DB_PATH = "messages.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS pending_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                message_id INTEGER NOT NULL
            )
        """)
        await db.commit()

async def save_pending(user_id: int, text: str, bot_message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO pending_messages (user_id, text, message_id) VALUES (?, ?, ?)",
            (user_id, text, bot_message_id)
        )
        await db.commit()

async def get_pending(message_id: int) -> Optional[tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id, text FROM pending_messages WHERE message_id = ?",
            (message_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return row

async def delete_pending(message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM pending_messages WHERE message_id = ?", (message_id,))
        await db.commit()
