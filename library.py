from typing import Any, List, Optional, Set, Sequence, Tuple  # noqa: F401

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

        params: Tuple[str, ...]
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
        return await cursor.fetchone() or (None, None)


async def getAnyQuoteById(database: DatabaseMain,
                          id: int
                          ) -> Tuple[Optional[str], Optional[str]]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT quote, broadcaster FROM quotes WHERE quoteId=?
'''
        await cursor.execute(query, (id,))
        return await cursor.fetchone() or (None, None)


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

        params: Tuple[str, ...]
        params = (' '.join(words),) + tuple(w.lower() for w in words)
        await cursor.execute(query, params)
        return await cursor.fetchone() or (None, None)


async def addQuote(database: DatabaseMain,
                   channel: str,
                   nick: str,
                   quote: str) -> int:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
INSERT INTO quotes (broadcaster, quote) VALUES (?, ?)
'''
        await cursor.execute(query, (channel, quote))
        await cursor.execute('SELECT lastval()')
        quoteId: int = int((await cursor.fetchone() or [0])[0])

        query = '''
INSERT INTO quotes_history (quoteId, createdTime, broadcaster, quote, editor)
    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
'''
        await cursor.execute(query, (quoteId, channel, quote, nick))
        await database.commit()
        return quoteId


async def updateQuote(database: DatabaseMain,
                      channel: str,
                      nick: str,
                      quoteId: int,
                      quote: str) -> bool:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
UPDATE quotes SET quote=? WHERE quoteId=? AND broadcaster=?
'''
        await cursor.execute(query, (quote, quoteId, channel))
        if cursor.rowcount == 0:
            return False

        query = '''
INSERT INTO quotes_history (quoteId, createdTime, broadcaster, quote, editor)
    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
'''
        await cursor.execute(query, (quoteId, channel, quote, nick))
        await database.commit()
        return True


async def deleteQuote(database: DatabaseMain,
                      channel: str,
                      quoteId: int) -> bool:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
DELETE FROM quotes WHERE quoteId=? AND broadcaster=?
'''
        await cursor.execute(query, (quoteId, channel))
        await database.commit()
        return cursor.rowcount != 0


async def copyQuote(database: DatabaseMain,
                    from_channel: str,
                    to_channel: str,
                    nick: str,
                    quoteId: int) -> bool:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT quote FROM quotes WHERE quoteId=? AND broadcaster=?
'''
        await cursor.execute(query, (id, from_channel))
        quote: Optional[str] = ((await cursor.fetchone()) or [None])[0]
        if quote is None:
            return False
        query = '''
INSERT INTO quotes (broadcaster, quote) VALUES (?, ?)
'''
        await cursor.execute(query, (to_channel, quote))
        await cursor.execute('SELECT lastval()')
        quoteId = int((await cursor.fetchone() or [0])[0])

        query = '''
SELECT tag FROM quotes_tags WHERE quoteId=?
'''
        quoteTagsParams: List[Tuple[int, str]]
        quoteTagsParams = [(quoteId, t) async for t,
                           in await cursor.execute(query, (id,))]
        query = '''
INSERT INTO quotes_tags (quoteId, tag) VALUES (?, ?)
'''
        await cursor.executemany(query, quoteTagsParams)

        query = '''
INSERT INTO quotes_history (quoteId, createdTime, broadcaster, quote, editor)
VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
'''
        await cursor.execute(query, (quoteId, to_channel, quote, nick))
        await database.commit()
        return True


async def getTagsOfQuote(database: DatabaseMain,
                         quoteId: int) -> Set[str]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
SELECT tag FROM quotes_tags WHERE quoteId=?
'''
        return {t async for t, in await cursor.execute(query, (quoteId,))}


async def addTagsToQuote(database: DatabaseMain,
                         quoteId: int,
                         tags: List[str]) -> bool:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
INSERT INTO quotes_tags (quoteId, tag) VALUES (?, ?)
'''
        await cursor.executemany(query, map(lambda t: (quoteId, t), tags))
        await database.commit()
        return cursor.rowcount != 0


async def deleteTagsToQuote(database: DatabaseMain,
                            quoteId: int,
                            tags: List[str]) -> bool:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
DELETE FROM quotes_tags WHERE quoteId=? AND tag=?
'''
        await cursor.executemany(query, map(lambda t: (quoteId, t), tags))
        await database.commit()
        return cursor.rowcount != 0


async def getQuoteIdsByWords(database: DatabaseMain,
                             channel: str,
                             words: Sequence[str]) -> List[int]:
    cursor: aioodbc.cursor.Cursor
    async with await database.cursor() as cursor:
        query: str = '''
    SELECT quoteId FROM quotes WHERE broadcaster=? AND quote MATCH ?
        UNION SELECT quoteId FROM quotes q WHERE broadcaster=? AND
    ''' + ' AND '.join(['? IN (SELECT tag FROM quotes_tags t '
                        'WHERE t.quoteId=q.quoteId)'] * len(words))
        query = 'SELECT quoteId FROM (' + query + ') ORDER BY quoteId ASC'
        params: Tuple[str, ...]
        params = (channel, ' '.join(words), channel,) + tuple(words)
        return [i async for i, in await cursor.execute(query, params)]
