import os

from tests.database.sqlite.test_database import TestSqlite
from .base_database import TestDatabaseQuotes


class TestLibraryQuoteSqlite(TestDatabaseQuotes, TestSqlite):
    async def setUp(self):
        await super().setUp()
        sqlFile = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'database-sqlite.sql')
        with open(sqlFile) as f:
            await self.execute(f.read())
        await self.setUpInsert()
