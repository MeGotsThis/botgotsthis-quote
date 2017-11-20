from datetime import datetime

import pyodbc

from tests.unittest.mock_class import TypeMatch
from ..library import database


class TestDatabaseQuotes:
    POOL_SIZE: int = 2

    async def setUpInsert(self):
        await self.execute('''
INSERT INTO quotes VALUES (1, 'megotsthis', 'Kappa')
''')
        await self.execute('''
INSERT INTO quotes_tags VALUES (1, 'Keepo')
''')

    async def tearDown(self):
        if self.database.isPostgres:
            await self.database.connection.rollback()
        await self.execute(['''DROP TABLE quotes_tags''',
                            '''DROP TABLE quotes''',
                            '''DROP TABLE quotes_history''',
                            ])
        await super().tearDown()

    async def test_get_random_quote(self):
        self.assertEqual(
            await database.getRandomQuote('megotsthis'),
            'Kappa')

    async def test_get_random_quote_empty(self):
        self.assertIsNone(
            await database.getRandomQuote('botgotsthis'))

    async def test_get_quote_id(self):
        self.assertEqual(
            await database.getQuoteById('megotsthis', 1),
            'Kappa')

    async def test_get_quote_id_empty(self):
        self.assertIsNone(
            await database.getQuoteById('botgotsthis', 1))
        self.assertIsNone(
            await database.getQuoteById('megotsthis', 0))

    async def test_get_quote_search(self):
        self.assertEqual(
            await database.getRandomQuoteBySearch('megotsthis', ['Kappa']),
            'Kappa')
        self.assertEqual(
            await database.getRandomQuoteBySearch('megotsthis', ['Keepo']),
            'Kappa')

    async def test_get_quote_search_empty(self):
        self.assertIsNone(
            await database.getRandomQuoteBySearch('megotsthis', ['FrankerZ']))
        self.assertIsNone(
            await database.getRandomQuoteBySearch('botgotsthis', ['Kappa']))

    async def test_get_any_random_quote(self):
        self.assertEqual(await database.getAnyRandomQuote(),
                         ('Kappa', 'megotsthis'))

    async def test_get_any_random_quote_empty(self):
        await self.execute('''DELETE FROM quotes''')
        self.assertEqual(await database.getAnyRandomQuote(),
                         (None, None))

    async def test_get_any_quote_id(self):
        self.assertEqual(await database.getAnyQuoteById(1),
                         ('Kappa', 'megotsthis'))

    async def test_get_any_quote_id_empty(self):
        self.assertEqual(await database.getAnyQuoteById(0),
                         (None, None))

    async def test_get_any_quote_search(self):
        self.assertEqual(
            await database.getAnyRandomQuoteBySearch(['Kappa']),
            ('Kappa', 'megotsthis'))
        self.assertEqual(
            await database.getAnyRandomQuoteBySearch(['Keepo']),
            ('Kappa', 'megotsthis'))

    async def test_get_any_quote_search_empty(self):
        self.assertEqual(
            await database.getAnyRandomQuoteBySearch(['FrankerZ']),
            (None, None))

    async def test_add_quote(self):
        self.assertEqual(
            await database.addQuote('megotsthis', 'botgotsthis', 'FrankerZ'),
            2)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa'),
                               (2, 'megotsthis', 'FrankerZ'),
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
                              [(1, 'megotsthis', 'FrankerZ'),
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
                              [(1, 'megotsthis', 'Kappa'),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])
        self.assertEqual(await self.rows('SELECT * FROM quotes_history'), [])

    async def test_delete_quote(self):
        self.assertEqual(
            await database.deleteQuote('megotsthis', 1),
            True)
        self.assertEqual(await self.rows('SELECT * FROM quotes'), [])
        self.assertEqual(await self.rows('SELECT * FROM quotes_tags'), [])
        self.assertEqual(await self.rows('SELECT * FROM quotes_history'), [])

    async def test_delete_quote_false(self):
        self.assertEqual(
            await database.deleteQuote('megotsthis', 2),
            False)
        self.assertEqual(
            await database.deleteQuote('botgotsthis', 1),
            False)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa'),
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
                              [(1, 'megotsthis', 'Kappa'),
                               (2, 'mebotsthis', 'Kappa'),
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
                              [(1, 'megotsthis', 'Kappa'),
                               (2, 'mebotsthis', 'Kappa'),
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
                              [(1, 'megotsthis', 'Kappa'),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])
        self.assertEqual(await self.rows('SELECT * FROM quotes_history'), [])

    async def test_get_tags(self):
        self.assertCountEqual(
            await database.getTagsOfQuote(1),
            ['Keepo'])

    async def test_get_tags_empty(self):
        await self.execute('''DELETE FROM quotes_tags''')
        self.assertCountEqual(
            await database.getTagsOfQuote(1), [])

    async def test_get_tags_no_quote(self):
        self.assertCountEqual(
            await database.getTagsOfQuote(2), [])

    async def test_add_tags(self):
        self.assertIs(
            await database.addTagsToQuote(1, ['FrankerZ', 'PogChamp']),
            True)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               (1, 'FrankerZ'),
                               (1, 'PogChamp'),
                               ])

    async def test_add_tags_false(self):
        self.assertIs(
            await database.addTagsToQuote(1, []),
            False)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])

    async def test_add_tags_error(self):
        with self.assertRaises(pyodbc.Error):
            await database.addTagsToQuote(1, ['Keepo'])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])

    async def test_delete_tags(self):
        self.assertIs(
            await database.deleteTagsToQuote(1, ['Keepo', 'FrankerZ']),
            True)
        self.assertEqual(await self.rows('SELECT * FROM quotes_tags'), [])

    async def test_delete_tags_false(self):
        self.assertIs(
            await database.deleteTagsToQuote(1, []),
            False)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])

    async def test_ids(self):
        self.assertCountEqual(
            await database.getQuoteIdsByWords('megotsthis', ['Keepo']),
            [1])
