from datetime import timedelta
from typing import Any, List, Optional, Set, Tuple  # noqa: F401

import aioodbc.cursor  # noqa: F401

import bot
import bot.utils
from lib.data import ChatCommandArgs
from lib.helper.chat import feature, permission
from lib.helper.message import messagesFromItems

from . import library


@feature('quotes')
async def commandQuote(args: ChatCommandArgs) -> bool:
    cooldown: timedelta = timedelta(seconds=30)
    if args.permissions.moderator:
        cooldown = timedelta(seconds=10)
    if (not args.permissions.broadcaster
            and 'quote' in args.chat.sessionData):
        since: timedelta = args.timestamp - args.chat.sessionData['quote']
        if since < cooldown:
            return False

    quote: Optional[str]
    if len(args.message) < 2:
        quote = await library.getRandomQuote(args.database, args.chat.channel)
        if quote is None:
            args.chat.send('There is no quotes added')
        else:
            args.chat.send(f'Quote: {quote}')
            args.chat.sessionData['quote'] = args.timestamp
    else:
        try:
            id: int = int(args.message[1])
            quote = await library.getQuoteById(
                args.database, args.chat.channel, id)
            if quote is None:
                args.chat.send('Cannot find that quote')
            else:
                args.chat.send(f'Quote: {quote}')
                args.chat.sessionData['quote'] = args.timestamp
        except ValueError:
            quote = await library.getRandomQuoteBySearch(
                args.database, args.chat.channel, list(args.message)[1:])
            if quote is None:
                args.chat.send('Cannot find a matching quote')
            else:
                args.chat.send('Quote: ' + quote)
                args.chat.sessionData['quote'] = args.timestamp
    return True


@permission('manager')
async def commandAnyQuote(args: ChatCommandArgs) -> bool:
    '''
    if 'anyquote-' in args.message.command:
        try:
            who = args.message.command.split('anyquote-')[1]
        except IndexError:
            who = None
    else:
        who = None
    '''
    msg: str
    quote: Optional[str]
    broadcaster: Optional[str]
    if len(args.message) < 2:
        quote, broadcaster = await library.getAnyRandomQuote(args.database)
        if quote is None:
            args.chat.send('There is no quotes added')
        else:
            msg = f'Quote from {broadcaster}: {quote}'
            if len(msg) > bot.config.messageLimit:
                args.chat.send(f'Quote: {quote}')
                args.chat.send(f'From: {broadcaster}')
            else:
                args.chat.send(msg)
    else:
        try:
            id: int = int(args.message[1])
            quote, broadcaster = await library.getAnyQuoteById(
                args.database, id)
            if quote is None:
                args.chat.send('Cannot find that quote')
            else:
                msg = f'Quote from {broadcaster}: {quote}'
                if len(msg) > bot.config.messageLimit:
                    args.chat.send('Quote: {quote}')
                    args.chat.send(f'From: {broadcaster}')
                else:
                    args.chat.send(msg)
        except ValueError:
            quote, broadcaster = await library.getAnyRandomQuoteBySearch(
                args.database, list(args.message)[1:])
            if quote is None:
                args.chat.send('Cannot find a matching quote')
            else:
                msg = f'Quote from {broadcaster}: {quote}'
                if len(msg) > bot.config.messageLimit:
                    args.chat.send(f'Quote: {quote}')
                    args.chat.send(f'From: {broadcaster}')
                else:
                    args.chat.send(msg)
    return True


@feature('quotes')
async def commandQuotes(args: ChatCommandArgs) -> bool:
    if len(args.message) == 1:
        args.chat.send(f'''\
Quotes List: http://megotsthis.com/botgotsthis/t/{args.chat.channel}/quotes''')
        return True

    if not args.permissions.moderator:
        return False

    if len(args.message) < 2:
        return False

    cursor: aioodbc.cursor.Cursor
    query: str
    params: Tuple[Any, ...]
    result: bool
    quote: str
    id: int
    quoteId: int
    if args.message.lower[1] in ['add', 'insert']:
        if len(args.message) < 3:
            return False

        quote = args.message[2:]
        try:
            quoteId = await library.addQuote(args.database, args.chat.channel,
                                             args.nick, quote)

            args.chat.send(f'''\
Quote has been added for {args.chat.channel} with quote id {quoteId}''')
            return True
        except Exception:
            bot.utils.logException(timestamp=args.timestamp)
            args.chat.send('Quote could not have been added')
    elif args.message.lower[1] in ['edit', 'update']:
        if len(args.message) < 4:
            return False

        quote = args.message[3:]
        try:
            id = int(args.message[2])
        except ValueError:
            args.chat.send('Quote could not been updated.')
            return True
        try:
            result = await library.updateQuote(
                args.database, args.chat.channel, args.nick, id, quote)
            if not result:
                args.chat.send(f'''\
Quote id {id} could not been updated. It may not exist.''')
                return True
            args.chat.send(f'''\
Quote id {id} has been update for {args.chat.channel}''')
            return True
        except Exception:
            bot.utils.logException(timestamp=args.timestamp)
            args.chat.send('Quote could not been updated.')
    elif args.message.lower[1] in ['del', 'delete', 'rem', 'remove']:
        if len(args.message) < 3:
            return False

        try:
            id = int(args.message[2])
        except ValueError:
            args.chat.send('Quote could not been deleted.')
            return True
        try:
            result = await library.deleteQuote(args.database,
                                               args.chat.channel, id)
            if not result:
                args.chat.send(f'''\
Quote id {id} could not been deleted. It may not exist.''')
                return True

            args.chat.send(f'''\
Quote id {id} has been deleted for {args.chat.channel}''')
            return True
        except Exception:
            bot.utils.logException(timestamp=args.timestamp)
            args.chat.send('Quote could not been deleted.')
    elif args.message.lower[1] in ['copy']:
        to: str
        if len(args.message) < 3:
            to = args.nick
        elif args.permissions.broadcaster:
            to = args.message.lower[3]
        else:
            return False
        if (to not in bot.globals.channels
                or not await args.database.hasFeature(to, 'quotes')):
            args.chat.send(f'''\
I am not in {to} or quotes feature is not enabled in {to}''')
            return True

        try:
            id = int(args.message[2])
        except ValueError:
            args.chat.send('Quote could not been copied.')
            return True
        try:
            quote = await library.getQuoteById(args.database,
                                               args.chat.channel, id)
            if quote is None:
                args.chat.send(f'''\
Quote id {id} could not been found. It may not exist.''')
                return True

            await library.copyQuote(args.database, args.chat.channel, to,
                                    args.nick, id)
            args.chat.send(f'''\
Quote id {id} has been copy for {to} with new id {quoteId}''')
            return True
        except Exception:
            bot.utils.logException(timestamp=args.timestamp)
            args.chat.send('Quote could not been copied.')
            return True
    elif args.message.lower[1] in ['tag', 'tags']:
        if len(args.message) < 3:
            return False

        try:
            id = int(args.message[2])
        except ValueError:
            args.chat.send('Quote could not been copied.')
            return True
        if len(args.message) >= 4:
            try:
                quoteTags: Tuple[str, ...] = tuple(args.message.lower)[3:]
                quote = await library.getQuoteById(args.database,
                                                   args.chat.channel, id)
                if quote is None:
                    args.chat.send(f'''\
Quote id {id} could not been found. It may not exist.''')
                    return True

                tags: Set[str]
                tags = await library.getTagsOfQuote(args.database, id)
                ignoreTags: List[str] = []
                addTags: List[str] = []
                deleteTags: List[str] = []
                tag: str
                for tag in quoteTags:
                    if tag[0] in '0123456789':
                        ignoreTags.append(tag)
                    if tag in tags:
                        deleteTags.append(tag)
                    else:
                        addTags.append(tag)
                if addTags:
                    await library.addTagsToQuote(args.database, id, addTags)
                if deleteTags:
                    await library.deleteTagsToQuote(args.database, id,
                                                    deleteTags)

                if addTags or deleteTags:
                    args.chat.send(f'Quote id {id} tags have been updated')
                    if ignoreTags:
                        args.chat.send(f'''\
These tags could not be used: {', '.join(ignoreTags)}''')
                else:
                    args.chat.send('No valid tags was specified')
            except Exception:
                bot.utils.logException(timestamp=args.timestamp)
                args.chat.send('Quote tags could not been updated.')
        else:
            try:
                quote = await library.getQuoteById(args.database,
                                                   args.chat.channel, id)
                if quote is None:
                    args.chat.send(f'''\
Quote id {id} could not been found. It may not exist.''')
                    return True
                tags = await library.getTagsOfQuote(args.database, id)
                if not tags:
                    args.chat.send('The quote does not have any tags')
                    return True
                args.chat.send(messagesFromItems(tags, 'Tags: '))
            except Exception:
                pass
    elif args.message.lower[1] in ['id', 'list']:
        if len(args.message) < 3:
            return False

        ids: List[int] = await library.getQuoteIdsByWords(
            args.database, args.chat.channel, list(args.message)[2:])
        quoteIds: List[str] = [str(i) for i in ids]
        if not quoteIds:
            args.chat.send('No quotes found with those parameters')
            return True
        args.chat.send(messagesFromItems(quoteIds, 'Possible IDs: '))
    return True
