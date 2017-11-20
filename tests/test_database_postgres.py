import os
from datetime import datetime

from tests.database.postgres.test_database import TestPostgres
from tests.unittest.mock_class import TypeMatch
from .base_database import TestDatabaseQuotes
from ..library import database


class TestLibraryQuotePostgres(TestDatabaseQuotes, TestPostgres):
    async def setUp(self):
        await super().setUp()
        sqlFile = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'database-postgres.sql')
        with open(sqlFile) as f:
            await self.execute(f.read())
        await self.setUpInsert()

    async def setUpInsert(self):
        await self.execute('''
INSERT INTO quotes VALUES (1, 'megotsthis', 'Kappa', to_tsvector('Kappa'))
''')
        await self.execute('''
INSERT INTO quotes_tags VALUES (1, 'Keepo')
''')
        await self.execute('''
ALTER SEQUENCE quotes_quoteid_seq RESTART WITH 2
''')
        docQuery = 'SELECT to_tsvector(?)'
        self.doc_kappa = (await self.row(docQuery, ('Kappa',)))[0]
        self.doc_frankerz = (await self.row(docQuery, ('FrankerZ',)))[0]

    async def test_add_quote(self):
        self.assertEqual(
            await database.addQuote('megotsthis', 'botgotsthis', 'FrankerZ'),
            2)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa', self.doc_kappa),
                               (2, 'megotsthis', 'FrankerZ',
                                self.doc_frankerz),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_history'),
                              [(1, 2, TypeMatch(datetime), 'megotsthis',
                                'FrankerZ', 'botgotsthis')])

    async def test_update_quote(self):
        self.assertEqual(
            await database.updateQuote('megotsthis', 'botgotsthis', 1,
                                       'FrankerZ'),
            True)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'FrankerZ',
                                self.doc_frankerz),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_history'),
                              [(1, 1, TypeMatch(datetime), 'megotsthis',
                                'FrankerZ', 'botgotsthis')])

    async def test_update_quote_false(self):
        self.assertEqual(
            await database.updateQuote('megotsthis', 'botgotsthis', 2,
                                       'FrankerZ'),
            False)
        self.assertEqual(
            await database.updateQuote('botgotsthis', 'botgotsthis', 1,
                                       'FrankerZ'),
            False)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa', self.doc_kappa),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])
        self.assertEqual(await self.rows('SELECT * FROM quotes_history'), [])

    async def test_delete_quote_false(self):
        self.assertEqual(
            await database.deleteQuote('megotsthis', 2),
            False)
        self.assertEqual(
            await database.deleteQuote('botgotsthis', 1),
            False)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa', self.doc_kappa),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])
        self.assertEqual(await self.rows('SELECT * FROM quotes_history'), [])

    async def test_copy_quote(self):
        self.assertEqual(
            await database.copyQuote('megotsthis', 'mebotsthis', 'botgotsthis',
                                     1),
            2)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa', self.doc_kappa),
                               (2, 'mebotsthis', 'Kappa', self.doc_kappa),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               (2, 'Keepo'),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_history'),
                              [(1, 2, TypeMatch(datetime), 'mebotsthis',
                                'Kappa', 'botgotsthis')])

    async def test_copy_quote_no_tags(self):
        await self.execute('''DELETE FROM quotes_tags''')
        self.assertEqual(
            await database.copyQuote('megotsthis', 'mebotsthis', 'botgotsthis',
                                     1),
            2)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa', self.doc_kappa),
                               (2, 'mebotsthis', 'Kappa', self.doc_kappa),
                               ])
        self.assertEqual(await self.rows('SELECT * FROM quotes_tags'), [])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_history'),
                              [(1, 2, TypeMatch(datetime), 'mebotsthis',
                                'Kappa', 'botgotsthis')])

    async def test_copy_quote_none(self):
        self.assertIsNone(
            await database.copyQuote('megotsthis', 'mebotsthis', 'botgotsthis',
                                     2))
        self.assertIsNone(
            await database.copyQuote('botgotsthis', 'mebotsthis',
                                     'botgotsthis', 1))
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa', self.doc_kappa),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])
        self.assertEqual(await self.rows('SELECT * FROM quotes_history'), [])
