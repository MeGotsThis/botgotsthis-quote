import encodings
from datetime import datetime

import pyodbc

from tests.unittest.mock_class import TypeMatch
from ..library import database

# Fix for running: python -m unittest discover -s ./pkg -t ./ -p test_*.py
encodings.search_function('utf-16le')


class TestDatabaseQuotes:
    async def setUpInsert(self):
        await self.execute('''
INSERT INTO quotes VALUES (1, 'megotsthis', 'Kappa')
''')
        await self.execute('''
INSERT INTO quotes_tags VALUES (1, 'Keepo')
''')

    async def tearDown(self):
        await self.execute(['''DROP TABLE quotes_tags''',
                            '''DROP TABLE quotes''',
                            '''DROP TABLE quotes_history''',
                            ])
        await super().tearDown()

    async def test_get_random_quote(self):
        self.assertEqual(
            await database.getRandomQuote(self.database, 'megotsthis'),
            'Kappa')

    async def test_get_random_quote_empty(self):
        self.assertIsNone(
            await database.getRandomQuote(self.database, 'botgotsthis'))

    async def test_get_quote_id(self):
        self.assertEqual(
            await database.getQuoteById(self.database, 'megotsthis', 1),
            'Kappa')

    async def test_get_quote_id_empty(self):
        self.assertIsNone(
            await database.getQuoteById(self.database, 'botgotsthis', 1))
        self.assertIsNone(
            await database.getQuoteById(self.database, 'megotsthis', 0))

    async def test_get_quote_search(self):
        self.assertEqual(
            await database.getRandomQuoteBySearch(self.database, 'megotsthis',
                                                  ['Kappa']),
            'Kappa')
        self.assertEqual(
            await database.getRandomQuoteBySearch(self.database, 'megotsthis',
                                                  ['Keepo']),
            'Kappa')

    async def test_get_quote_search_empty(self):
        self.assertIsNone(
            await database.getRandomQuoteBySearch(self.database, 'megotsthis',
                                                  ['FrankerZ']))
        self.assertIsNone(
            await database.getRandomQuoteBySearch(self.database, 'botgotsthis',
                                                  ['Kappa']))

    async def test_get_any_random_quote(self):
        self.assertEqual(await database.getAnyRandomQuote(self.database),
                         ('Kappa', 'megotsthis'))

    async def test_get_any_random_quote_empty(self):
        await self.execute('''DELETE FROM quotes''')
        self.assertEqual(await database.getAnyRandomQuote(self.database),
                         (None, None))

    async def test_get_any_quote_id(self):
        self.assertEqual(await database.getAnyQuoteById(self.database, 1),
                         ('Kappa', 'megotsthis'))

    async def test_get_any_quote_id_empty(self):
        self.assertEqual(await database.getAnyQuoteById(self.database, 0),
                         (None, None))

    async def test_get_any_quote_search(self):
        self.assertEqual(
            await database.getAnyRandomQuoteBySearch(self.database, ['Kappa']),
            ('Kappa', 'megotsthis'))
        self.assertEqual(
            await database.getAnyRandomQuoteBySearch(self.database, ['Keepo']),
            ('Kappa', 'megotsthis'))

    async def test_get_any_quote_search_empty(self):
        self.assertEqual(
            await database.getAnyRandomQuoteBySearch(self.database,
                                                     ['FrankerZ']),
            (None, None))

    async def test_add_quote(self):
        self.assertEqual(
            await database.addQuote(self.database, 'megotsthis', 'botgotsthis',
                                    'FrankerZ'),
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
            await database.updateQuote(self.database, 'megotsthis',
                                       'botgotsthis', 1, 'FrankerZ'),
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
            await database.updateQuote(self.database, 'megotsthis',
                                       'botgotsthis', 2, 'FrankerZ'),
            False)
        self.assertEqual(
            await database.updateQuote(self.database, 'botgotsthis',
                                       'botgotsthis', 1, 'FrankerZ'),
            False)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa'),
                               ])
        self.assertEqual(await self.rows('SELECT * FROM quotes_history'), [])

    async def test_delete_quote(self):
        self.assertEqual(
            await database.deleteQuote(self.database, 'megotsthis', 1),
            True)
        self.assertEqual(await self.rows('SELECT * FROM quotes'), [])
        self.assertEqual(await self.rows('SELECT * FROM quotes_tags'), [])
        self.assertEqual(await self.rows('SELECT * FROM quotes_history'), [])

    async def test_delete_quote_false(self):
        self.assertEqual(
            await database.deleteQuote(self.database, 'megotsthis', 2),
            False)
        self.assertEqual(
            await database.deleteQuote(self.database, 'botgotsthis', 1),
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
            await database.copyQuote(self.database, 'megotsthis',
                                     'mebotsthis', 'botgotsthis', 1),
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
            await database.copyQuote(self.database, 'megotsthis',
                                     'mebotsthis', 'botgotsthis', 1),
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
            await database.copyQuote(self.database, 'megotsthis',
                                     'mebotsthis', 'botgotsthis', 2))
        self.assertIsNone(
            await database.copyQuote(self.database, 'botgotsthis',
                                     'mebotsthis', 'botgotsthis', 1))
        self.assertCountEqual(await self.rows('SELECT * FROM quotes'),
                              [(1, 'megotsthis', 'Kappa'),
                               ])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])
        self.assertEqual(await self.rows('SELECT * FROM quotes_history'), [])

    async def test_get_tags(self):
        self.assertCountEqual(
            await database.getTagsOfQuote(self.database, 1),
            ['Keepo'])

    async def test_get_tags_empty(self):
        await self.execute('''DELETE FROM quotes_tags''')
        self.assertCountEqual(
            await database.getTagsOfQuote(self.database, 1), [])

    async def test_get_tags_no_quote(self):
        self.assertCountEqual(
            await database.getTagsOfQuote(self.database, 2), [])

    async def test_add_tags(self):
        self.assertIs(
            await database.addTagsToQuote(self.database, 1,
                                          ['FrankerZ', 'PogChamp']),
            True)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               (1, 'FrankerZ'),
                               (1, 'PogChamp'),
                               ])

    async def test_add_tags_false(self):
        self.assertIs(
            await database.addTagsToQuote(self.database, 1, []),
            False)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])

    async def test_add_tags_error(self):
        with self.assertRaises(pyodbc.Error):
            await database.addTagsToQuote(self.database, 1,
                                          ['Keepo'])
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])

    async def test_delete_tags(self):
        self.assertIs(
            await database.deleteTagsToQuote(self.database, 1,
                                             ['Keepo', 'FrankerZ']),
            True)
        self.assertEqual(await self.rows('SELECT * FROM quotes_tags'), [])

    async def test_delete_tags_false(self):
        self.assertIs(
            await database.deleteTagsToQuote(self.database, 1, []),
            False)
        self.assertCountEqual(await self.rows('SELECT * FROM quotes_tags'),
                              [(1, 'Keepo'),
                               ])

    async def test_ids(self):
        self.assertCountEqual(
            await database.getQuoteIdsByWords(self.database, 'megotsthis',
                                              ['Keepo']),
            [1])
