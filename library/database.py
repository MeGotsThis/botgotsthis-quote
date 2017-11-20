from typing import Any, List, Optional, Set, Sequence, Tuple  # noqa: F401

import aioodbc.cursor  # noqa: F401

from lib.database import DatabaseMain


async def getRandomQuote(channel: str) -> Optional[str]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
SELECT quote FROM quotes WHERE broadcaster=? ORDER BY random() LIMIT 1
'''
        await cursor.execute(query, (channel,))
        return (await cursor.fetchone() or [None])[0]


async def getQuoteById(channel: str,
                       id: int) -> Optional[str]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
SELECT quote FROM quotes WHERE broadcaster=? AND quoteId=?
'''
        await cursor.execute(query, (channel, id))
        return (await cursor.fetchone() or [None])[0]


async def getRandomQuoteBySearch(channel: str,
                                 words: Sequence[str]) -> Optional[str]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str
        params: Tuple[str, ...]
        if db.isPostgres:
            query = '''
SELECT quoteId FROM quotes WHERE broadcaster=? AND document @@ to_tsquery(?)
    UNION SELECT quoteId FROM quotes q WHERE broadcaster=? AND
''' + ' AND '.join(['? IN (SELECT LOWER(tag) FROM quotes_tags AS t '
                    'WHERE t.quoteId=q.quoteId)'] * len(words))
            query = '''
SELECT quote FROM quotes
    WHERE quoteId=(
        SELECT quoteId FROM (%s) AS q ORDER BY RANDOM() LIMIT 1)''' % query
            params = ((channel, ' | '.join(words), channel,)
                      + tuple(w.lower() for w in words))
            await cursor.execute(query, params)
            return (await cursor.fetchone() or [None])[0]

        query = '''
SELECT quoteId FROM quotes WHERE broadcaster=? AND
''' + ' AND '.join(['quote LIKE ?'] * len(words)) + '''
    UNION SELECT quoteId FROM quotes q WHERE broadcaster=? AND
''' + ' AND '.join(['? IN (SELECT LOWER(tag) FROM quotes_tags AS t '
                    'WHERE t.quoteId=q.quoteId)'] * len(words))
        query = '''
SELECT quote FROM quotes
    WHERE quoteId=(
        SELECT quoteId FROM (%s) AS q ORDER BY RANDOM() LIMIT 1)''' % query
        params = ((channel,) + tuple(f'%{w}%' for w in words) + (channel,)
                  + tuple(w.lower() for w in words))
        await cursor.execute(query, params)
        return (await cursor.fetchone() or [None])[0]


async def getAnyRandomQuote() -> Tuple[Optional[str], Optional[str]]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
SELECT quote, broadcaster FROM quotes ORDER BY random() LIMIT 1
'''
        await cursor.execute(query)
        row: Optional[Tuple[str, str]] = await cursor.fetchone()
        return (row[0], row[1]) if row else (None, None)


async def getAnyQuoteById(id: int
                          ) -> Tuple[Optional[str], Optional[str]]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
SELECT quote, broadcaster FROM quotes WHERE quoteId=?
'''
        await cursor.execute(query, (id,))
        row: Optional[Tuple[str, str]] = await cursor.fetchone()
        return (row[0], row[1]) if row else (None, None)


async def getAnyRandomQuoteBySearch(words: Sequence[str]
                                    ) -> Tuple[Optional[str], Optional[str]]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str
        params: Tuple[str, ...]
        row: Optional[Tuple[str, str]]
        if db.isPostgres:
            query = '''
SELECT quoteId FROM quotes WHERE document @@ to_tsquery(?)
    UNION SELECT quoteId FROM quotes q WHERE
''' + ' AND '.join(['? IN (SELECT LOWER(tag) FROM quotes_tags AS t '
                    'WHERE t.quoteId=q.quoteId)'] * len(words))
            query = '''
SELECT quote, broadcaster FROM quotes
    WHERE quoteId=(
        SELECT quoteId FROM (%s) AS q ORDER BY RANDOM() LIMIT 1)''' % query
            params = ((' | '.join(words),) + tuple(w.lower() for w in words))
            await cursor.execute(query, params)
            row = await cursor.fetchone()
            return (row[0], row[1]) if row else (None, None)

        query = '''
SELECT quoteId FROM quotes WHERE 1=1 AND
''' + ' AND '.join(['quote LIKE ?'] * len(words)) + '''
    UNION SELECT quoteId FROM quotes q WHERE 1=1 AND
''' + ' AND '.join(['? IN (SELECT LOWER(tag) FROM quotes_tags AS t '
                    'WHERE t.quoteId=q.quoteId)'] * len(words))
        query = f'''
SELECT quote, broadcaster FROM quotes WHERE quoteId=(
    SELECT quoteId FROM ({query}) AS q ORDER BY RANDOM() LIMIT 1)
'''
        params = (tuple(f'%{w}%' for w in words)
                  + tuple(w.lower() for w in words))
        await cursor.execute(query, params)
        row = await cursor.fetchone()
        return (row[0], row[1]) if row else (None, None)


async def addQuote(channel: str,
                   nick: str,
                   quote: str) -> int:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str
        quoteId: int
        if db.isPostgres:
            query = '''
INSERT INTO quotes (broadcaster, quote, document) VALUES (?, ?, to_tsvector(?))
'''
            await cursor.execute(query, (channel, quote, quote))
            await cursor.execute('SELECT lastval()')
            quoteId = int((await cursor.fetchone() or [0])[0])
        else:
            query = '''
INSERT INTO quotes (broadcaster, quote) VALUES (?, ?)
'''
            await cursor.execute(query, (channel, quote))
            await cursor.execute('SELECT last_insert_rowid()')
            quoteId = int((await cursor.fetchone() or [0])[0])

        query = '''
INSERT INTO quotes_history (quoteId, createdTime, broadcaster, quote, editor)
    VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
'''
        await cursor.execute(query, (quoteId, channel, quote, nick))
        await db.commit()
        return quoteId


async def updateQuote(channel: str,
                      nick: str,
                      quoteId: int,
                      quote: str) -> bool:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str
        if db.isPostgres:
            query = '''
UPDATE quotes SET quote=?, document=to_tsvector(?)
    WHERE quoteId=? AND broadcaster=?
            '''
            await cursor.execute(query, (quote, quote, quoteId, channel))
        else:
            query = '''
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
        await db.commit()
        return True


async def deleteQuote(channel: str,
                      quoteId: int) -> bool:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
DELETE FROM quotes WHERE quoteId=? AND broadcaster=?
'''
        await cursor.execute(query, (quoteId, channel))
        await db.commit()
        return cursor.rowcount != 0


async def copyQuote(from_channel: str,
                    to_channel: str,
                    nick: str,
                    quoteId: int) -> Optional[int]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
SELECT quote FROM quotes WHERE quoteId=? AND broadcaster=?
'''
        await cursor.execute(query, (quoteId, from_channel))
        quote: Optional[str] = ((await cursor.fetchone()) or [None])[0]
        if quote is None:
            return None
        newQuoteId: int
        if db.isPostgres:
            query = '''
INSERT INTO quotes (broadcaster, quote, document) VALUES (?, ?, to_tsvector(?))
'''
            await cursor.execute(query, (to_channel, quote, quote))
            await cursor.execute('SELECT lastval()')
            newQuoteId = int((await cursor.fetchone() or [0])[0])
        else:
            query = '''
INSERT INTO quotes (broadcaster, quote) VALUES (?, ?)
'''
            await cursor.execute(query, (to_channel, quote))
            await cursor.execute('SELECT last_insert_rowid()')
            newQuoteId = int((await cursor.fetchone() or [0])[0])

        query = '''
SELECT tag FROM quotes_tags WHERE quoteId=?
'''
        quoteTagsParams: List[Tuple[int, str]]
        quoteTagsParams = [(newQuoteId, t) async for t,
                           in await cursor.execute(query, (quoteId,))]
        if quoteTagsParams:
            query = '''
INSERT INTO quotes_tags (quoteId, tag) VALUES (?, ?)
'''
            await cursor.executemany(query, quoteTagsParams)

        query = '''
INSERT INTO quotes_history (quoteId, createdTime, broadcaster, quote, editor)
VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
'''
        await cursor.execute(query, (newQuoteId, to_channel, quote, nick))
        await db.commit()
        return newQuoteId


async def getTagsOfQuote(quoteId: int) -> Set[str]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
SELECT tag FROM quotes_tags WHERE quoteId=?
'''
        return {t async for t, in await cursor.execute(query, (quoteId,))}


async def addTagsToQuote(quoteId: int,
                         tags: List[str]) -> bool:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
INSERT INTO quotes_tags (quoteId, tag) VALUES (?, ?)
'''
        await cursor.executemany(query, map(lambda t: (quoteId, t), tags))
        await db.commit()
        return bool(tags)


async def deleteTagsToQuote(quoteId: int,
                            tags: List[str]) -> bool:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
DELETE FROM quotes_tags WHERE quoteId=? AND tag=?
'''
        await cursor.executemany(query, map(lambda t: (quoteId, t), tags))
        await db.commit()
        return bool(tags)


async def getQuoteIdsByWords(channel: str,
                             words: Sequence[str]) -> List[int]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str
        params: Tuple[str, ...]
        if db.isPostgres:
            query = '''
SELECT quoteId FROM quotes WHERE broadcaster=? AND document @@ to_tsquery(?)
    UNION SELECT quoteId FROM quotes q WHERE broadcaster=? AND
''' + ' AND '.join(['? IN (SELECT LOWER(tag) FROM quotes_tags AS t '
                    'WHERE t.quoteId=q.quoteId)'] * len(words))
            query = '''
SELECT quoteId FROM (%s) AS q ORDER BY quoteId ASC
''' % query
            params = ((channel, ' | '.join(words), channel,)
                      + tuple(w.lower() for w in words))
            await cursor.execute(query, params)
            return [i async for i, in await cursor.execute(query, params)]

        query = '''
SELECT quoteId FROM quotes WHERE broadcaster=? AND
''' + ' AND '.join(['quote LIKE ?'] * len(words)) + '''
    UNION SELECT quoteId FROM quotes q WHERE broadcaster=? AND
''' + ' AND '.join(['? IN (SELECT LOWER(tag) FROM quotes_tags AS t '
                    'WHERE t.quoteId=q.quoteId)'] * len(words))
        query = 'SELECT quoteId FROM (' + query + ') AS q ORDER BY quoteId ASC'
        params = ((channel,) + tuple(f'%{w}%' for w in words) + (channel,)
                  + tuple(w.lower() for w in words))
        return [i async for i, in await cursor.execute(query, params)]
