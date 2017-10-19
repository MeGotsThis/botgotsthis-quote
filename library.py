from typing import Any, Optional, Sequence, Tuple  # noqa: F401

import aioodbc.cursor  # noqa: F401

from lib.database import DatabaseMain


async def getRandomQuote(database: DatabaseMain,
                         channel: str) -> Optional[str]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT quote FROM quotes WHERE broadcaster=? ORDER BY random() LIMIT 1
'''
        await cursor.execute(query, (channel,))
        return (await cursor.fetchone() or [None])[0]


async def getQuoteById(database: DatabaseMain,
                       channel: str,
                       id: int) -> Optional[str]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT quote FROM quotes WHERE broadcaster=? AND quoteId=?
'''
        await cursor.execute(query, (channel, id))
        return (await cursor.fetchone() or [None])[0]


async def getRandomQuoteBySearch(database: DatabaseMain,
                                 channel: str,
                                 words: Sequence[str]) -> Optional[str]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        where: str
        where = ' AND '.join(['? IN (SELECT tag FROM quotes_tags t '
                              'WHERE t.quoteId=q.quoteId)'] * len(words))
        query = ('''
SELECT quoteId FROM quotes WHERE broadcaster=? AND quote MATCH ?
UNION SELECT quoteId FROM quotes q WHERE broadcaster=? AND ''' + where)
        query = '''
SELECT quote FROM quotes
    WHERE quoteId=(
        SELECT quoteId FROM (%s) ORDER BY RANDOM() LIMIT 1)''' % query

        params: Tuple[Any, ...]
        params = ((channel, ' '.join(words), channel,)
                  + tuple(w.lower() for w in words))
        await cursor.execute(query, params)
        return (await cursor.fetchone() or [None])[0]


async def getAnyRandomQuote(database: DatabaseMain
                            ) -> Tuple[Optional[str], Optional[str]]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT quote, broadcaster FROM quotes ORDER BY random() LIMIT 1
'''
        await cursor.execute(query)
        return await cursor.fetchone() or [None, None]


async def getAnyQuoteById(database: DatabaseMain,
                          id: int
                          ) -> Tuple[Optional[str], Optional[str]]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT quote, broadcaster FROM quotes WHERE quoteId=?
'''
        await cursor.execute(query, (id,))
        return await cursor.fetchone() or [None, None]


async def getAnyRandomQuoteBySearch(database: DatabaseMain,
                                    words: Sequence[str]
                                    ) -> Tuple[Optional[str], Optional[str]]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str
        where: str
        where = ' AND '.join(['? IN (SELECT tag FROM quotes_tags t '
                              'WHERE t.quoteId=q.quoteId)'] * len(words))
        query = f'''
SELECT quoteId FROM quotes WHERE quote MATCH ?
    UNION SELECT quoteId FROM quotes q WHERE {where}
'''
        query = f'''
SELECT quote, broadcaster FROM quotes WHERE quoteId=(
    SELECT docid FROM ({query}) ORDER BY RANDOM() LIMIT 1)
'''

        params: Tuple[Any, ...]
        params = (' '.join(words),) + tuple(w.lower() for w in words)
        await cursor.execute(query, params)
        return (await cursor.fetchone() or [None])[0]
