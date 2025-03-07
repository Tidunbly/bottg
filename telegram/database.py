import aiosqlite


class DataBase:
    def __init__(self):
        self.connection = None

    async def init(self):
        await self.create_connection()
        await self.create_table()
        await self.create_table_rates()
        await self.create_table_admins()

    async def create_connection(self):
        self.connection = await aiosqlite.connect('query_database.db')

    async def create_table(self):
        async with aiosqlite.connect('query_database.db') as con:
            await con.execute('''CREATE TABLE IF NOT EXISTS queries
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 user_id INTEGER,
                                 query TEXT,
                                 answer TEXT DEFAULT NULL,
                                 place TEXT DEFAULT NULL,
                                 status TEXT,
                                 admin_id INTEGER DEFAULT NULL)''')

    async def create_table_rates(self):
        async with aiosqlite.connect('query_database.db') as con:
            await con.execute('''CREATE TABLE IF NOT EXISTS rating
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 query_id INTEGER,
                                 query TEXT,
                                 rate INTEGER DEFAULT NULL)''')



    async def create_table_admins(self):
        async with aiosqlite.connect('query_database.db') as con:
            await con.execute('''CREATE TABLE IF NOT EXISTS admins
                                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                 admin_id INTEGER,
                                 status TEXT)''')


    async def add_admin(self, admin_id: int, status: str = "active"):
        async with aiosqlite.connect('query_database.db') as con:
            await con.execute('''
                INSERT INTO admins (admin_id, status)
                VALUES (?, ?)
            ''', (admin_id, status))
            await con.commit()

    async def is_admin_exists(self, admin_id: int) -> bool:
        async with aiosqlite.connect('query_database.db') as con:
            cursor = await con.execute('''
                SELECT 1 FROM admins WHERE admin_id = ?
            ''', (admin_id,))
            result = await cursor.fetchone()
            return result is not None

    async def get_admin_status(self, admin_id: int) -> str:
        async with aiosqlite.connect('query_database.db') as con:
            cursor = await con.execute('''
                SELECT status FROM admins WHERE admin_id = ?
            ''', (admin_id,))
            result = await cursor.fetchone()
            return result[0] if result else None

    async def get_active_admins(self):
        """
        Возвращает список ID всех активных администраторов.
        :return: Список ID администраторов.
        """
        async with aiosqlite.connect('query_database.db') as con:
            cursor = await con.execute('SELECT admin_id FROM admins WHERE status = ?', ('active',))
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def update_admin_status(self, admin_id: int, new_status: str):
        async with aiosqlite.connect('query_database.db') as con:
            await con.execute('''
                UPDATE admins SET status = ? WHERE admin_id = ?
            ''', (new_status, admin_id))
            await con.commit()

    async def delete_admin(self, admin_id: int):
        async with aiosqlite.connect('query_database.db') as con:
            await con.execute('''
                DELETE FROM admins WHERE admin_id = ?
            ''', (admin_id,))
            await con.commit()

    async def is_admins_table_empty(self) -> bool:
        if self.connection is None:
            await self.create_connection()

        async with self.connection.execute('SELECT COUNT(*) FROM admins') as cursor:
            row = await cursor.fetchone()
            count = row[0] if row else 0

        return count == 0

    async def add_query_to_rating(self, query_id: int, query: str):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute(
                'INSERT INTO rating (query_id, query) VALUES (?, ?)',
                (query_id, query)):
            await self.connection.commit()

    async def get_all_rates(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM rating ORDER BY id DESC') as cursor:
            rows = await cursor.fetchall()
            return rows

    async def add_rate_to_query(self, rate: int, query_id: int):
        async with self.connection.execute(
                'UPDATE rating SET rate = ? WHERE query_id = ?',
                (rate, query_id)):
            await self.connection.commit()

    # добавление запроса
    async def add_query(self, user_id: int, query: str, place: str, answer: str, status: str):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute(
                'INSERT INTO queries (user_id, query, answer, place, status) VALUES (?, ?, ?, ?, ?)',
                (user_id, query, answer, place, status)) as cursor:
            await self.connection.commit()
            return cursor.lastrowid

    async def get_unanswered_query(self):

        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute("SELECT * FROM queries WHERE status = ? ORDER BY id DESC", ('Не решён',)) as cursor:
            rows = await cursor.fetchall()
            return rows

    async def get_answered_query(self):

        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute("SELECT * FROM queries WHERE status = ? ORDER BY id DESC", ('Решён',)) as cursor:
            rows = await cursor.fetchall()
            return rows

    async def update_query_id(self, query_id: int, answer: str, status: str):

        async with self.connection.execute('UPDATE queries SET answer = ?, status = ? WHERE id = ?',
                                           (answer, status, query_id)):
            await self.connection.commit()

    async def update_query_response(self, query_id: int, answer: str):

        async with self.connection.execute('UPDATE queries SET answer = ? WHERE id = ?',
                                           (answer, query_id)):
            await self.connection.commit()

    async def update_query_status(self, query_id: int, status: str, admin_id: int):
        async with self.connection.execute(
                'UPDATE queries SET status = ?, admin_id = ? WHERE id = ?',
                (status, admin_id, query_id)
        ):
            await self.connection.commit()

    async def get_query_by_id(self, query_id):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM queries WHERE id = ?', (query_id,)) as cursor:
            row = await cursor.fetchone()
            return row

    async def get_admin_id(self, query_id):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT admin_id FROM queries WHERE id = ?', (query_id,)) as cursor:
            row = await cursor.fetchone()
            return row

    async def get_all_query(self):
        if self.connection is None:
            await self.create_connection()
        async with self.connection.execute('SELECT * FROM queries ORDER BY id ASC') as cursor:
            rows = await cursor.fetchall()
            return rows

    async def get_query(self, query_id: int):
        async with self.connection.execute('SELECT user_id, query, answer FROM queries WHERE id = ?',
                                           (query_id,)) as cursor:
            row = await cursor.fetchone()
            if row is not None:
                user_id, query, answer = row
                return {'user_id': user_id, 'query': query, 'answer': answer}
            else:
                return None


    async def delete_query(self, query_id: int):
        async with self.connection.execute('DELETE FROM queries WHERE id = ?', (query_id,)):
            await self.connection.execute('DELETE FROM sqlite_sequence WHERE name="queries"')
            await self.connection.commit()
