import aiosqlite


class DataBase:
    def __init__(self):
        self.connection = None

    async def init(self):
        await self.create_connection()
        await self.create_table()
        await self.create_table_rates()

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
