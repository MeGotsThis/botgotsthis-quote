﻿from typing import Iterable, Mapping, Optional

from lib.data import ChatCommand

from .. import channel


def filterMessage() -> Iterable[ChatCommand]:
    return []


def commands() -> Mapping[str, Optional[ChatCommand]]:
    if not hasattr(commands, 'commands'):
        setattr(commands, 'commands', {
            '!quote': channel.commandQuote,
            '!anyquote': channel.commandAnyQuote,
            '!allquote': channel.commandAnyQuote,
            '!quotes': channel.commandQuotes,
            }
        )
    return getattr(commands, 'commands')


def commandsStartWith() -> Mapping[str, Optional[ChatCommand]]:
    return {}


def processNoCommand() -> Iterable[ChatCommand]:
    return []
