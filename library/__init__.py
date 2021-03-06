from datetime import timedelta
from typing import List, Optional, Set  # noqa: F401

import pyodbc

import bot
from lib.data import ChatCommandArgs
from lib.helper import message
from . import database as db_helper


async def quoteInCooldown(args: ChatCommandArgs) -> bool:
    cooldown: timedelta = timedelta(seconds=30)
    if args.permissions.moderator:
        cooldown = timedelta(seconds=10)
    if (not args.permissions.broadcaster
            and 'quote' in args.chat.sessionData):
        since: timedelta = args.timestamp - args.chat.sessionData['quote']
        if since < cooldown:
            return True
    return False


async def quoteMarkCooldown(args: ChatCommandArgs) -> None:
    if ('quote' not in args.chat.sessionData
            or args.timestamp > args.chat.sessionData['quote']):
        args.chat.sessionData['quote'] = args.timestamp


async def processRandomQuote(args: ChatCommandArgs) -> bool:
    quote: Optional[str]
    quote = await db_helper.getRandomQuote(args.chat.channel)
    if quote is None:
        args.chat.send('There is no quotes added')
        return False
    args.chat.send(f'Quote: {quote}')
    return True


async def processQuoteId(args: ChatCommandArgs, quoteId: int) -> bool:
    quote: Optional[str]
    quote = await db_helper.getQuoteById(args.chat.channel, quoteId)
    if quote is None:
        args.chat.send('Cannot find that quote')
    else:
        args.chat.send(f'Quote: {quote}')
    return True


async def processRandomQuoteSearch(args: ChatCommandArgs,
                                   words: List[str]) -> bool:
    quote: Optional[str]
    quote = await db_helper.getRandomQuoteBySearch(args.chat.channel, words)
    if quote is None:
        args.chat.send('Cannot find a matching quote')
    else:
        args.chat.send(f'Quote: {quote}')
    return True


async def processAnyRandomQuote(args: ChatCommandArgs) -> bool:
    quote: Optional[str]
    broadcaster: Optional[str]
    quote, broadcaster = await db_helper.getAnyRandomQuote()
    if quote is None:
        args.chat.send('There is no quotes added')
    else:
        assert broadcaster is not None
        sendQuoteWithBroadcaster(args, broadcaster, quote)
    return True


async def processAnyQuoteId(args: ChatCommandArgs, quoteId: int) -> bool:
    quote: Optional[str]
    broadcaster: Optional[str]
    quote, broadcaster = await db_helper.getAnyQuoteById(quoteId)
    if quote is None:
        args.chat.send('Cannot find that quote')
    else:
        assert broadcaster is not None
        sendQuoteWithBroadcaster(args, broadcaster, quote)
    return True


async def processAnyRandomQuoteSearch(args: ChatCommandArgs,
                                      words: List[str]) -> bool:
    quote: Optional[str]
    broadcaster: Optional[str]
    quote, broadcaster = await db_helper.getAnyRandomQuoteBySearch(words)
    if quote is None:
        args.chat.send('Cannot find a matching quote')
    else:
        assert broadcaster is not None
        sendQuoteWithBroadcaster(args, broadcaster, quote)
    return True


async def sendQuoteWithBroadcaster(args: ChatCommandArgs, broadcaster: str,
                                   quote: str) -> None:
    msg: str = f'Quote from {broadcaster}: {quote}'
    if len(msg) > bot.config.messageLimit:
        args.chat.send(f'Quote: {quote}')
        args.chat.send(f'From: {broadcaster}')
    else:
        args.chat.send(msg)


async def handleQuoteList(args: ChatCommandArgs) -> bool:
    args.chat.send(f'''\
Quotes List: http://megotsthis.com/botgotsthis/t/{args.chat.channel}/quotes''')
    return True


async def handleAddQuote(args: ChatCommandArgs) -> bool:
    if len(args.message) < 3:
        return False

    quote: str = args.message[2:]
    try:
        quoteId: int
        quoteId = await db_helper.addQuote(args.chat.channel, args.nick, quote)

        args.chat.send(f'''\
Quote has been added for {args.chat.channel} with quote id {quoteId}''')
    except pyodbc.Error:
        args.chat.send('Quote could not have been added')
        raise
    return True


async def handleEditQuote(args: ChatCommandArgs) -> bool:
    if len(args.message) < 4:
        return False

    id: int
    quote: str = args.message[3:]
    try:
        id = int(args.message[2])
    except ValueError:
        args.chat.send('Quote id is not a number.')
        return True
    try:
        result: bool = await db_helper.updateQuote(
            args.chat.channel, args.nick, id, quote)
        if not result:
            args.chat.send(f'''\
Quote id {id} could not been updated. It may not exist.''')
            return True
        args.chat.send(f'''\
Quote id {id} has been updated for {args.chat.channel}''')
    except pyodbc.Error:
        args.chat.send('Quote could not been updated.')
        raise
    return True


async def handleDeleteQuote(args: ChatCommandArgs) -> bool:
    if len(args.message) < 3:
        return False

    id: int
    try:
        id = int(args.message[2])
    except ValueError:
        args.chat.send('Quote id is not a number.')
        return True
    try:
        result = await db_helper.deleteQuote(args.chat.channel, id)
        if not result:
            args.chat.send(f'''\
Quote id {id} could not been deleted. It may not exist.''')
            return True

        args.chat.send(f'''\
Quote id {id} has been deleted for {args.chat.channel}''')
    except pyodbc.Error:
        args.chat.send('Quote could not been deleted.')
        raise
    return True


async def handleCopyQuote(args: ChatCommandArgs) -> bool:
    if len(args.message) < 3:
        return False

    id: int
    try:
        id = int(args.message[2])
    except ValueError:
        args.chat.send('Quote id is not a number.')
        return True

    to: str
    if len(args.message) == 3:
        to = args.nick
    elif args.permissions.broadcaster and len(args.message) >= 4:
        to = args.message.lower[3]
    else:
        return False
    if (to not in bot.globals.channels
            or not await args.data.hasFeature(to, 'quotes')):
        args.chat.send(f'''\
I am not in {to} or quotes feature is not enabled in {to}''')
        return True

    quote: str
    try:
        quote = await db_helper.getQuoteById(args.chat.channel, id)
        if quote is None:
            args.chat.send(f'''\
Quote id {id} could not been found. It may not exist.''')
            return True

        quoteId: Optional[int] = await db_helper.copyQuote(
            args.chat.channel, to, args.nick, id)
        if quoteId is None:
            args.chat.send('Quote could not been copied.')
            return True
        args.chat.send(f'''\
Quote id {id} has been copied for {to} with new id {quoteId}''')
    except pyodbc.Error:
        args.chat.send('Quote could not been copied.')
        raise
    return True


async def handleTagQuote(args: ChatCommandArgs) -> bool:
    if len(args.message) < 3:
        return False

    id: int
    try:
        id = int(args.message[2])
    except ValueError:
        args.chat.send('Quote id is not a number.')
        return True
    if len(args.message) >= 4:
        quoteTags: List[str] = list(args.message.lower)[3:]
        return await processQuoteTags(args, id, quoteTags)
    else:
        return await processListQuoteTags(args, id)


async def processQuoteTags(args: ChatCommandArgs,
                           quoteId: int,
                           tags: List[str]) -> bool:
    try:
        quote = await db_helper.getQuoteById(args.chat.channel, quoteId)
        if quote is None:
            args.chat.send(f'''\
Quote id {quoteId} could not been found. It may not exist.''')
            return True

        currentTags: Set[str]
        currentTags = await db_helper.getTagsOfQuote(quoteId)
        ignoreTags: List[str] = []
        addTags: List[str] = []
        deleteTags: List[str] = []
        tag: str
        for tag in tags:
            if tag[0] in '0123456789':
                ignoreTags.append(tag)
                continue
            if tag in currentTags:
                deleteTags.append(tag)
            else:
                addTags.append(tag)
        if addTags:
            await db_helper.addTagsToQuote(quoteId, addTags)
        if deleteTags:
            await db_helper.deleteTagsToQuote(quoteId, deleteTags)

        if addTags or deleteTags:
            args.chat.send(f'Quote id {quoteId} tags have been updated')
        if ignoreTags:
            args.chat.send(f'''\
These tags could not be used: {', '.join(ignoreTags)}''')
        if not addTags and not deleteTags and not ignoreTags:
            args.chat.send('No valid tags was specified')
    except pyodbc.Error:
        args.chat.send('Quote tags could not been updated.')
        raise
    return True


async def processListQuoteTags(args: ChatCommandArgs,
                               quoteId: int) -> bool:
    try:
        quote = await db_helper.getQuoteById(args.chat.channel, quoteId)
        if quote is None:
            args.chat.send(f'''\
Quote id {quoteId} could not been found. It may not exist.''')
            return True
        tags = await db_helper.getTagsOfQuote(quoteId)
        if not tags:
            args.chat.send('The quote does not have any tags')
            return True
        args.chat.send(message.messagesFromItems(tags, 'Tags: '))
    except pyodbc.Error:
        args.chat.send('Unknown error.')
        raise
    return True


async def handleListQuoteIds(args: ChatCommandArgs) -> bool:
    if len(args.message) < 3:
        return False

    try:
        ids: List[int] = await db_helper.getQuoteIdsByWords(
            args.chat.channel, list(args.message)[2:])
        quoteIds: List[str] = [str(i) for i in ids]
        if not quoteIds:
            args.chat.send('No quotes found with those parameters')
            return True
        args.chat.send(message.messagesFromItems(quoteIds, 'Possible IDs: '))
    except pyodbc.Error:
        args.chat.send('Unknown error.')
        raise
    return True
