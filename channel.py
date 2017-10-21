from typing import List  # noqa: F401

from lib.data import ChatCommandArgs
from lib.helper.chat import feature, permission

from . import library


@feature('quotes')
async def commandQuote(args: ChatCommandArgs) -> bool:
    if library.quoteInCooldown(args):
        return False

    quoteSent: bool = False
    if len(args.message) < 2:
        quoteSent = await library.processRandomQuote(args)
    else:
        try:
            quoteId: int = int(args.message[1])
        except ValueError:
            words: List[str] = list(args.message)[1:]
            quoteSent = await library.processRandomQuoteSearch(args, words)
        else:
            quoteSent = await library.processQuoteId(args, quoteId)
    if quoteSent:
        await library.quoteMarkCooldown(args)
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
    if len(args.message) < 2:
        await library.processAnyRandomQuote(args)
    else:
        try:
            quoteId: int = int(args.message[1])
        except ValueError:
            words: List[str] = list(args.message)[1:]
            await library.processAnyRandomQuoteSearch(args, words)
        else:
            await library.processAnyQuoteId(args, quoteId)
    return True


@feature('quotes')
async def commandQuotes(args: ChatCommandArgs) -> bool:
    if len(args.message) == 1:
        return await library.handleQuoteList(args)

    if not args.permissions.moderator:
        return False

    if len(args.message) < 2:
        return False

    if args.message.lower[1] in ['add', 'insert']:
        return await library.handleAddQuote(args)
    elif args.message.lower[1] in ['edit', 'update']:
        return await library.handleEditQuote(args)
    elif args.message.lower[1] in ['del', 'delete', 'rem', 'remove']:
        return await library.handleDeleteQuote(args)
    elif args.message.lower[1] in ['copy']:
        return await library.handleCopyQuote(args)
    elif args.message.lower[1] in ['tag', 'tags']:
        return await library.handleTagQuote(args)
    elif args.message.lower[1] in ['id', 'list']:
        return await library.handleListQuoteIds(args)
    return True
