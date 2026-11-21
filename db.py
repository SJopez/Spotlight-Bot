import sqlite3

class DataBase():
    def __init__(self):
        self.linker = sqlite3.connect(":memory:")
        
        self.linker.execute("""
            CREATE TABLE IF NOT EXISTS replies (
                chat_id INTEGER NOT NULL, 
                i INTEGER NOT NULL, 
                j INTEGER NOT NULL,
                n INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, i, j)
            )
        """)

        self.linker.execute("""
            CREATE TABLE IF NOT EXISTS active_chats (
                chat_id INTEGER PRIMARY KEY
            )
        """)

        self.linker.execute("""
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                first_name TEXT,
                username TEXT,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

    def add_reply(self, chat, i, j):
        self.linker.execute("""
            INSERT INTO replies (chat_id, i, j, n) VALUES (?, ?, ?, 1)
            ON CONFLICT(chat_id, i, j) DO UPDATE SET n = n + 1
        """, (chat, i, j))
        self.linker.commit()

    def add_user(self, chat, user_id, first_name, username):
        self.linker.execute("""
            INSERT INTO users (chat_id, user_id, first_name, username) VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET first_name = excluded.first_name, username = excluded.username
        """, (chat, user_id, first_name, username))
        self.linker.commit()

    def active_chat(self, chat):
        self.linker.execute("INSERT OR IGNORE INTO active_chats (chat_id) VALUES (?)", (chat,))
        self.linker.commit()

    def count_users(self, chat):
        return self.linker.execute("SELECT COUNT(*) FROM users WHERE chat_id = ?", (chat,)).fetchone()[0]

    def join_chat(self, chat):
        return self.linker.execute("SELECT chat_id FROM active_chats WHERE chat_id = ?", (chat,)).fetchone()

    def get_replies(self, chat):
        return self.linker.execute(
            "SELECT * FROM replies WHERE chat_id = ? ORDER BY n DESC", (chat,)
        ).fetchall()

    def get_names(self, chat):
        rows = self.linker.execute(
            "SELECT user_id, first_name, username FROM users WHERE chat_id = ?", (chat,)
        ).fetchall()
        return {user_id: (username or first_name) for user_id, first_name, username in rows}

    def add_replies(self, chat, counts):
        self.linker.executemany("""
            INSERT INTO replies (chat_id, i, j, n) VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id, i, j) DO UPDATE SET n = n + excluded.n
        """, [(chat, i, j, n) for (i, j), n in counts.items()])
        self.linker.commit()

    def add_users_if_missing(self, chat, names):
        self.linker.executemany(
            "INSERT OR IGNORE INTO users (chat_id, user_id, first_name, username) VALUES (?, ?, ?, NULL)",
            [(chat, user_id, name) for user_id, name in names.items()]
        )
        self.linker.commit()

    def get_user_ids(self, chat):
        rows = self.linker.execute("SELECT user_id FROM users WHERE chat_id = ?", (chat,)).fetchall()
        return [row[0] for row in rows]

    def remove_users(self, chat, ids):
        self.linker.executemany(
            "DELETE FROM replies WHERE chat_id = ? AND (i = ? OR j = ?)",
            [(chat, user_id, user_id) for user_id in ids]
        )
        self.linker.executemany(
            "DELETE FROM users WHERE chat_id = ? AND user_id = ?",
            [(chat, user_id) for user_id in ids]
        )
        self.linker.commit()