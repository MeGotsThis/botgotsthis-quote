from datetime import timedelta

import pyodbc
from asynctest.mock import patch

from tests.unittest.base_channel import TestChannel
from tests.unittest.mock_class import StrContains
from lib.data.message import Message

from .. import library
from ..library import database


class TestLibraryQuoteBase(TestChannel):
    pass


class TestLibraryQuoteCooldown(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()
        self.permissions.moderator = True
        self.permissions.broadcaster = False

    async def test(self):
        self.assertIs(await library.quoteInCooldown(self.args), False)

    async def test_cooldown(self):
        self.channel.sessionData['quote'] = self.now
        self.assertIs(await library.quoteInCooldown(self.args), True)

    async def test_old(self):
        self.channel.sessionData['quote'] = self.now - timedelta(seconds=31)
        self.assertIs(await library.quoteInCooldown(self.args), False)

    async def test_moderator_cooldown(self):
        self.permissions.moderator = True
        self.channel.sessionData['quote'] = self.now
        self.assertIs(await library.quoteInCooldown(self.args), True)

    async def test_moderator(self):
        self.permissions.moderator = True
        self.channel.sessionData['quote'] = self.now - timedelta(seconds=11)
        self.assertIs(await library.quoteInCooldown(self.args), False)

    async def test_broadcaster(self):
        self.permissions.broadcaster = True
        self.channel.sessionData['quote'] = self.now
        self.assertIs(await library.quoteInCooldown(self.args), False)

    async def test_broadcaster_new(self):
        self.permissions.broadcaster = True
        self.assertIs(await library.quoteInCooldown(self.args), False)

    async def test_mark(self):
        await library.quoteMarkCooldown(self.args)
        self.assertEqual(self.channel.sessionData['quote'], self.now)

    async def test_mark_override(self):
        self.channel.sessionData['quote'] = self.now - timedelta(days=1)
        await library.quoteMarkCooldown(self.args)
        self.assertEqual(self.channel.sessionData['quote'], self.now)

    async def test_mark_old(self):
        self.channel.sessionData['quote'] = self.now + timedelta(days=1)
        await library.quoteMarkCooldown(self.args)
        self.assertEqual(self.channel.sessionData['quote'],
                         self.now + timedelta(days=1))


class TestLibraryQuoteProcessRandomQuote(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(database.__name__ + '.getRandomQuote')
        self.addCleanup(patcher.stop)
        self.mock_getter = patcher.start()

    async def test(self):
        self.mock_getter.return_value = 'Kappa'
        self.assertIs(await library.processRandomQuote(self.args), True)
        self.channel.send.assert_called_once_with(
            StrContains('Quote', 'Kappa'))

    async def test_no_quote(self):
        self.mock_getter.return_value = None
        self.assertIs(await library.processRandomQuote(self.args), False)
        self.channel.send.assert_called_once_with(
            StrContains('no', 'quotes'))


class TestLibraryQuoteProcessQuoteId(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(database.__name__ + '.getQuoteById')
        self.addCleanup(patcher.stop)
        self.mock_getter = patcher.start()

    async def test(self):
        self.mock_getter.return_value = 'Kappa'
        self.assertIs(await library.processQuoteId(self.args, 0), True)
        self.channel.send.assert_called_once_with(
            StrContains('Quote', 'Kappa'))

    async def test_no_quote(self):
        self.mock_getter.return_value = None
        self.assertIs(await library.processQuoteId(self.args, 0), True)
        self.channel.send.assert_called_once_with(
            StrContains('Cannot', 'find', 'quote'))


class TestLibraryQuoteProcessQuoteSearch(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(database.__name__ + '.getRandomQuoteBySearch')
        self.addCleanup(patcher.stop)
        self.mock_getter = patcher.start()

    async def test(self):
        self.mock_getter.return_value = 'Kappa'
        self.assertIs(
            await library.processRandomQuoteSearch(self.args, ['Kappa']),
            True)
        self.channel.send.assert_called_once_with(
            StrContains('Quote', 'Kappa'))

    async def test_no_quote(self):
        self.mock_getter.return_value = None
        self.assertIs(
            await library.processRandomQuoteSearch(self.args, ['Kappa']),
            True)
        self.channel.send.assert_called_once_with(
            StrContains('Cannot', 'find', 'quote'))


class TestLibraryQuoteProcessAnyRandomQuote(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(library.__name__ + '.sendQuoteWithBroadcaster')
        self.addCleanup(patcher.stop)
        self.mock_send = patcher.start()

        patcher = patch(database.__name__ + '.getAnyRandomQuote')
        self.addCleanup(patcher.stop)
        self.mock_getter = patcher.start()

    async def test(self):
        self.mock_getter.return_value = 'Kappa', 'megotsthis'
        self.assertIs(await library.processAnyRandomQuote(self.args), True)
        self.mock_send.assert_called_once_with(
            self.args, 'megotsthis', 'Kappa')

    async def test_no_quote(self):
        self.mock_getter.return_value = None, None
        self.assertIs(await library.processAnyRandomQuote(self.args), True)
        self.channel.send.assert_called_once_with(StrContains('no', 'quotes'))


class TestLibraryQuoteProcessAnyQuoteId(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(library.__name__ + '.sendQuoteWithBroadcaster')
        self.addCleanup(patcher.stop)
        self.mock_send = patcher.start()

        patcher = patch(database.__name__ + '.getAnyQuoteById')
        self.addCleanup(patcher.stop)
        self.mock_getter = patcher.start()

    async def test(self):
        self.mock_getter.return_value = 'Kappa', 'megotsthis'
        self.assertIs(await library.processAnyQuoteId(self.args, 0), True)
        self.mock_send.assert_called_once_with(
            self.args, 'megotsthis', 'Kappa')

    async def test_no_quote(self):
        self.mock_getter.return_value = None, None
        self.assertIs(await library.processAnyQuoteId(self.args, 0), True)
        self.channel.send.assert_called_once_with(
            StrContains('Cannot', 'find', 'quote'))


class TestLibraryQuoteProcessAnyQuoteSearch(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(library.__name__ + '.sendQuoteWithBroadcaster')
        self.addCleanup(patcher.stop)
        self.mock_send = patcher.start()

        patcher = patch(database.__name__ + '.getAnyRandomQuoteBySearch')
        self.addCleanup(patcher.stop)
        self.mock_getter = patcher.start()

    async def test(self):
        self.mock_getter.return_value = 'Kappa', 'megotsthis'
        self.assertIs(
            await library.processAnyRandomQuoteSearch(self.args, ['Kappa']),
            True)
        self.mock_send.assert_called_once_with(
            self.args, 'megotsthis', 'Kappa')

    async def test_no_quote(self):
        self.mock_getter.return_value = None, None
        self.assertIs(
            await library.processAnyRandomQuoteSearch(self.args, ['Kappa']),
            True)
        self.channel.send.assert_called_once_with(
            StrContains('Cannot', 'find', 'quote'))


class TestLibraryQuoteSendQuoteWithBroadcaster(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch('bot.config')
        self.addCleanup(patcher.stop)
        self.mock_config = patcher.start()
        self.mock_config.messageLimit = 500

    async def test(self):
        await library.sendQuoteWithBroadcaster(self.args, 'megotsthis',
                                               'Kappa')
        self.channel.send.assert_called_once_with(
            StrContains('megotsthis', 'Kappa'))

    async def test_small_limit(self):
        self.mock_config.messageLimit = 20
        await library.sendQuoteWithBroadcaster(self.args, 'megotsthis',
                                               'Kappa')
        self.assertEqual(self.channel.send.call_count, 2)
        self.channel.send.assert_any_call(StrContains('megotsthis'))
        self.channel.send.assert_any_call(StrContains('Kappa'))


class TestLibraryQuoteHandleList(TestLibraryQuoteBase):
    async def test(self):
        self.assertIs(await library.handleQuoteList(self.args), True)
        self.channel.send.assert_called_once_with(
            StrContains('http', self.channel.channel))


class TestLibraryQuoteHandleAdd(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(database.__name__ + '.addQuote')
        self.addCleanup(patcher.stop)
        self.mock_adder = patcher.start()

    async def test_no_arg(self):
        self.args = self.args._replace(message=Message('!quotes add'))
        self.assertIs(await library.handleAddQuote(self.args), False)
        self.assertFalse(self.mock_adder.called)
        self.assertFalse(self.channel.send.called)

    async def test(self):
        self.mock_adder.return_value = 0
        self.args = self.args._replace(message=Message('!quotes add Kappa'))
        self.assertIs(await library.handleAddQuote(self.args), True)
        self.assertTrue(self.mock_adder.called)
        self.channel.send.assert_called_once_with(
            StrContains(self.channel.channel, 'added', '0'))

    async def test_except(self):
        self.mock_adder.side_effect = pyodbc.Error
        self.args = self.args._replace(message=Message('!quotes add Kappa'))
        with self.assertRaises(pyodbc.Error):
            await library.handleAddQuote(self.args)
        self.assertTrue(self.mock_adder.called)
        self.channel.send.assert_called_once_with(
            StrContains('not', 'added'))


class TestLibraryQuoteHandleEdit(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(database.__name__ + '.updateQuote')
        self.addCleanup(patcher.stop)
        self.mock_updater = patcher.start()

    async def test_no_arg(self):
        self.args = self.args._replace(message=Message('!quotes edit 0'))
        self.assertIs(await library.handleEditQuote(self.args), False)
        self.assertFalse(self.mock_updater.called)
        self.assertFalse(self.channel.send.called)

    async def test_not_number(self):
        self.args = self.args._replace(message=Message('!quotes edit a Kappa'))
        self.assertIs(await library.handleEditQuote(self.args), True)
        self.assertFalse(self.mock_updater.called)
        self.channel.send.assert_called_once_with(StrContains('not', 'number'))

    async def test(self):
        self.mock_updater.return_value = True
        self.args = self.args._replace(message=Message('!quotes edit 0 Kappa'))
        self.assertIs(await library.handleEditQuote(self.args), True)
        self.assertTrue(self.mock_updater.called)
        self.channel.send.assert_called_once_with(
            StrContains(self.channel.channel, 'updated', '0'))

    async def test_false(self):
        self.mock_updater.return_value = False
        self.args = self.args._replace(message=Message('!quotes edit 0 Kappa'))
        self.assertIs(await library.handleEditQuote(self.args), True)
        self.assertTrue(self.mock_updater.called)
        self.channel.send.assert_called_once_with(
            StrContains('not', 'updated'))

    async def test_except(self):
        self.mock_updater.side_effect = pyodbc.Error
        self.args = self.args._replace(message=Message('!quotes edit 0 Kappa'))
        with self.assertRaises(pyodbc.Error):
            await library.handleEditQuote(self.args)
        self.assertTrue(self.mock_updater.called)
        self.channel.send.assert_called_once_with(
            StrContains('not', 'updated'))


class TestLibraryQuoteHandleDelete(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(database.__name__ + '.deleteQuote')
        self.addCleanup(patcher.stop)
        self.mock_deleter = patcher.start()

    async def test_no_arg(self):
        self.args = self.args._replace(message=Message('!quotes delete'))
        self.assertIs(await library.handleDeleteQuote(self.args), False)
        self.assertFalse(self.mock_deleter.called)
        self.assertFalse(self.channel.send.called)

    async def test_not_number(self):
        self.args = self.args._replace(message=Message('!quotes delete a'))
        self.assertIs(await library.handleDeleteQuote(self.args), True)
        self.assertFalse(self.mock_deleter.called)
        self.channel.send.assert_called_once_with(StrContains('not', 'number'))

    async def test(self):
        self.mock_deleter.return_value = True
        self.args = self.args._replace(message=Message('!quotes delete 0'))
        self.assertIs(await library.handleDeleteQuote(self.args), True)
        self.assertTrue(self.mock_deleter.called)
        self.channel.send.assert_called_once_with(
            StrContains(self.channel.channel, 'deleted', '0'))

    async def test_false(self):
        self.mock_deleter.return_value = False
        self.args = self.args._replace(message=Message('!quotes delete 0'))
        self.assertIs(await library.handleDeleteQuote(self.args), True)
        self.assertTrue(self.mock_deleter.called)
        self.channel.send.assert_called_once_with(
            StrContains('not', 'deleted'))

    async def test_except(self):
        self.mock_deleter.side_effect = pyodbc.Error
        self.args = self.args._replace(message=Message('!quotes delete 0'))
        with self.assertRaises(pyodbc.Error):
            await library.handleDeleteQuote(self.args)
        self.assertTrue(self.mock_deleter.called)
        self.channel.send.assert_called_once_with(
            StrContains('not', 'deleted'))


class TestLibraryQuoteHandleCopy(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        self.permissions.broadcaster = True
        self.features.append('quotes')

        patcher = patch('bot.globals')
        self.addCleanup(patcher.stop)
        self.mock_globals = patcher.start()
        self.mock_globals.channels = {
            'botgotsthis': object()
        }

        patcher = patch(database.__name__ + '.getQuoteById')
        self.addCleanup(patcher.stop)
        self.mock_getter = patcher.start()
        self.mock_getter.return_value = 'Kappa'

        patcher = patch(database.__name__ + '.copyQuote')
        self.addCleanup(patcher.stop)
        self.mock_copier = patcher.start()

    async def test_no_arg(self):
        self.args = self.args._replace(message=Message('!quotes copy'))
        self.assertIs(await library.handleCopyQuote(self.args), False)
        self.assertFalse(self.mock_copier.called)
        self.assertFalse(self.channel.send.called)

    async def test_not_number(self):
        self.args = self.args._replace(message=Message('!quotes copy a'))
        self.assertIs(await library.handleCopyQuote(self.args), True)
        self.assertFalse(self.mock_copier.called)
        self.channel.send.assert_called_once_with(StrContains('not', 'number'))

    async def test_no_permission(self):
        self.permissions.broadcaster = False
        self.args = self.args._replace(
            message=Message('!quotes copy 0 botgotsthis'))
        self.assertIs(await library.handleCopyQuote(self.args), False)
        self.assertFalse(self.mock_copier.called)
        self.assertFalse(self.channel.send.called)

    async def test_no_quotes(self):
        self.features.clear()
        self.args = self.args._replace(message=Message('!quotes copy 0'))
        self.assertIs(await library.handleCopyQuote(self.args), True)
        self.assertFalse(self.mock_copier.called)
        self.channel.send.assert_called_once_with(
            StrContains('not', 'botgotsthis', 'enabled'))

    async def test_no_channel(self):
        self.args = self.args._replace(
            message=Message('!quotes copy 0 megotsthis'))
        self.assertIs(await library.handleCopyQuote(self.args), True)
        self.assertFalse(self.mock_copier.called)
        self.channel.send.assert_called_once_with(
            StrContains('not', 'megotsthis', 'enabled'))

    async def test_no_quote(self):
        self.mock_getter.return_value = None
        self.args = self.args._replace(
            message=Message('!quotes copy 0 megotsthis'))
        self.assertIs(await library.handleCopyQuote(self.args), True)
        self.assertFalse(self.mock_copier.called)
        self.channel.send.assert_called_once_with(
            StrContains('not', 'megotsthis', 'enabled'))

    async def test(self):
        self.mock_copier.return_value = 1
        self.args = self.args._replace(message=Message('!quotes copy 0'))
        self.assertIs(await library.handleCopyQuote(self.args), True)
        self.assertTrue(self.mock_copier.called)
        self.channel.send.assert_called_once_with(
            StrContains(self.channel.channel, 'copied', '0', '1'))

    async def test_except(self):
        self.mock_copier.side_effect = pyodbc.Error
        self.args = self.args._replace(message=Message('!quotes copy 0'))
        with self.assertRaises(pyodbc.Error):
            await library.handleCopyQuote(self.args)
        self.assertTrue(self.mock_copier.called)
        self.channel.send.assert_called_once_with(
            StrContains('not', 'copied'))


class TestLibraryQuoteHandleTag(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch(library.__name__ + '.processQuoteTags')
        self.addCleanup(patcher.stop)
        self.mock_quoteTags = patcher.start()

        patcher = patch(library.__name__ + '.processListQuoteTags')
        self.addCleanup(patcher.stop)
        self.mock_listTags = patcher.start()

    async def test_no_arg(self):
        self.args = self.args._replace(message=Message('!quotes tag'))
        self.assertIs(await library.handleTagQuote(self.args), False)
        self.assertFalse(self.mock_quoteTags.called)
        self.assertFalse(self.mock_listTags.called)
        self.assertFalse(self.channel.send.called)

    async def test_not_number(self):
        self.args = self.args._replace(message=Message('!quotes tag a'))
        self.assertIs(await library.handleTagQuote(self.args), True)
        self.assertFalse(self.mock_quoteTags.called)
        self.assertFalse(self.mock_listTags.called)
        self.channel.send.assert_called_once_with(StrContains('not', 'number'))

    async def test(self):
        self.mock_listTags.return_value = True
        self.args = self.args._replace(message=Message('!quotes tag 0'))
        self.assertIs(await library.handleTagQuote(self.args), True)
        self.assertFalse(self.mock_quoteTags.called)
        self.assertTrue(self.mock_listTags.called)

    async def test_process(self):
        self.mock_quoteTags.return_value = True
        self.args = self.args._replace(message=Message('!quotes tag 0 Kappa'))
        self.assertIs(await library.handleTagQuote(self.args), True)
        self.assertTrue(self.mock_quoteTags.called)
        self.assertFalse(self.mock_listTags.called)


class TestLibraryQuoteProcessTags(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch('lib.helper.message.messagesFromItems')
        self.addCleanup(patcher.stop)
        self.mock_message = patcher.start()
        self.mock_message.return_value = ['Kappa']

        patcher = patch(database.__name__ + '.getQuoteById')
        self.addCleanup(patcher.stop)
        self.mock_getId = patcher.start()
        self.mock_getId.return_value = 0

        patcher = patch(database.__name__ + '.getTagsOfQuote')
        self.addCleanup(patcher.stop)
        self.mock_listTags = patcher.start()

        patcher = patch(database.__name__ + '.addTagsToQuote')
        self.addCleanup(patcher.stop)
        self.mock_adder = patcher.start()

        patcher = patch(database.__name__ + '.deleteTagsToQuote')
        self.addCleanup(patcher.stop)
        self.mock_deleter = patcher.start()

    async def test_no_quote(self):
        self.mock_getId.return_value = None
        self.args = self.args._replace(message=Message('!quotes id'))
        self.assertIs(await library.processQuoteTags(self.args, 0, ['Kappa']),
                      True)
        self.assertFalse(self.mock_listTags.called)
        self.assertFalse(self.mock_adder.called)
        self.assertFalse(self.mock_deleter.called)
        self.channel.send.assert_called_once_with(
            StrContains('0', 'not', 'found'))

    async def test(self):
        self.mock_listTags.return_value = ['Kappa']
        self.args = self.args._replace(
            message=Message('!quotes tag 0 Kappa FrankerZ'))
        self.assertIs(
            await library.processQuoteTags(self.args, 0,
                                           ['Kappa', 'FrankerZ']),
            True)
        self.assertTrue(self.mock_listTags.called)
        self.mock_adder.asset_called_once_with(self.database, 0, ['FrankerZ'])
        self.mock_deleter.asset_called_once_with(self.database, 0, ['Kappa'])
        self.channel.send.assert_called_once_with(
            StrContains('0', 'tags', 'updated'))

    async def test_number(self):
        self.mock_listTags.return_value = []
        self.args = self.args._replace(
            message=Message('!quotes tag 0 0abc'))
        self.assertIs(await library.processQuoteTags(self.args, 0, ['0abc']),
                      True)
        self.assertTrue(self.mock_listTags.called)
        self.assertFalse(self.mock_adder.called)
        self.assertFalse(self.mock_deleter.called)
        self.channel.send.assert_called_once_with(
            StrContains('tags', 'use', '0abc'))

    async def test_empty(self):
        self.mock_listTags.return_value = []
        self.args = self.args._replace(message=Message('!quotes tag 0 Kappa'))
        self.assertIs(await library.processQuoteTags(self.args, 0, []),
                      True)
        self.assertTrue(self.mock_listTags.called)
        self.assertFalse(self.mock_adder.called)
        self.assertFalse(self.mock_deleter.called)
        self.channel.send.assert_called_once_with(
            StrContains('No', 'valid', 'tags'))

    async def test_except(self):
        self.mock_listTags.side_effect = pyodbc.Error
        self.args = self.args._replace(message=Message('!quotes tag 0 Kappa'))
        with self.assertRaises(pyodbc.Error):
            await library.processQuoteTags(self.args, 0, ['Kappa'])
        self.assertTrue(self.mock_listTags.called)
        self.assertFalse(self.mock_adder.called)
        self.assertFalse(self.mock_deleter.called)
        self.channel.send.assert_called_once_with(
            StrContains('tags', 'not', 'updated'))


class TestLibraryQuoteProcessListTags(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch('lib.helper.message.messagesFromItems')
        self.addCleanup(patcher.stop)
        self.mock_message = patcher.start()
        self.mock_message.return_value = ['Kappa']

        patcher = patch(database.__name__ + '.getQuoteById')
        self.addCleanup(patcher.stop)
        self.mock_getId = patcher.start()
        self.mock_getId.return_value = 0

        patcher = patch(database.__name__ + '.getTagsOfQuote')
        self.addCleanup(patcher.stop)
        self.mock_listTags = patcher.start()

    async def test_no_quote(self):
        self.mock_getId.return_value = None
        self.args = self.args._replace(message=Message('!quotes id'))
        self.assertIs(await library.processListQuoteTags(self.args, 0), True)
        self.assertFalse(self.mock_listTags.called)
        self.channel.send.assert_called_once_with(
            StrContains('0', 'not', 'found'))

    async def test(self):
        self.mock_listTags.return_value = [0]
        self.args = self.args._replace(message=Message('!quotes id Kappa'))
        self.assertIs(await library.processListQuoteTags(self.args, 0), True)
        self.assertTrue(self.mock_listTags.called)
        self.channel.send.assert_called_once_with(['Kappa'])

    async def test_empty(self):
        self.mock_listTags.return_value = []
        self.args = self.args._replace(message=Message('!quotes id Kappa'))
        self.assertIs(await library.processListQuoteTags(self.args, 0), True)
        self.assertTrue(self.mock_listTags.called)
        self.channel.send.assert_called_once_with(
            StrContains('quote', 'tags'))

    async def test_except(self):
        self.mock_listTags .side_effect = pyodbc.Error
        self.args = self.args._replace(message=Message('!quotes id Kappa'))
        with self.assertRaises(pyodbc.Error):
            await library.processListQuoteTags(self.args, 0)
        self.assertTrue(self.mock_listTags.called)
        self.channel.send.assert_called_once_with(StrContains('error'))


class TestLibraryQuoteHandleId(TestLibraryQuoteBase):
    def setUp(self):
        super().setUp()

        patcher = patch('lib.helper.message.messagesFromItems')
        self.addCleanup(patcher.stop)
        self.mock_message = patcher.start()
        self.mock_message.return_value = ['Kappa']

        patcher = patch(database.__name__ + '.getQuoteIdsByWords')
        self.addCleanup(patcher.stop)
        self.mock_lister = patcher.start()

    async def test_no_arg(self):
        self.args = self.args._replace(message=Message('!quotes id'))
        self.assertIs(await library.handleListQuoteIds(self.args), False)
        self.assertFalse(self.mock_lister.called)
        self.assertFalse(self.channel.send.called)

    async def test(self):
        self.mock_lister.return_value = [0]
        self.args = self.args._replace(message=Message('!quotes id Kappa'))
        self.assertIs(await library.handleListQuoteIds(self.args), True)
        self.assertTrue(self.mock_lister.called)
        self.channel.send.assert_called_once_with(['Kappa'])

    async def test_empty(self):
        self.mock_lister.return_value = []
        self.args = self.args._replace(message=Message('!quotes id Kappa'))
        self.assertIs(await library.handleListQuoteIds(self.args), True)
        self.assertTrue(self.mock_lister.called)
        self.channel.send.assert_called_once_with(
            StrContains('No', 'quotes', 'found'))

    async def test_except(self):
        self.mock_lister.side_effect = pyodbc.Error
        self.args = self.args._replace(message=Message('!quotes id Kappa'))
        with self.assertRaises(pyodbc.Error):
            await library.handleListQuoteIds(self.args)
        self.assertTrue(self.mock_lister.called)
        self.channel.send.assert_called_once_with(StrContains('error'))
