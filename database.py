import aiosqlite

DB_PATH = "bot_data.db"


async def init_db() -> None:
    """Inicializa as tabelas do banco de dados SQLite."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                rep INTEGER NOT NULL DEFAULT 0,
                coins INTEGER NOT NULL DEFAULT 0,
                last_rep_at REAL NOT NULL DEFAULT 0
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS ticket_counter (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_number INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        await db.execute("INSERT OR IGNORE INTO ticket_counter (id, last_number) VALUES (1, 0)")
        await db.commit()


async def next_ticket_number() -> int:
    """Retorna e incrementa o número sequencial de tickets."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE ticket_counter SET last_number = last_number + 1 WHERE id = 1")
        await db.commit()
        async with db.execute("SELECT last_number FROM ticket_counter WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 1
