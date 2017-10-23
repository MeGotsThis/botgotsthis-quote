from asynctest.mock import patch

from tests.unittest.base_channel import TestChannel
from lib.data.message import Message

# Needs to be imported last
from .. import library
from .. import channel


class TestChannelQuoteQuote(TestChannel):
    def setUp(self):
        super().setUp()

        self.features.append('quotes')

        patcher = patch(library.__name__ + '.quoteInCooldown')
        self.addCleanup(patcher.stop)
        self.mock_inCooldown = patcher.start()
        self.mock_inCooldown.return_value = False

        patcher = patch(library.__name__ + '.quoteMarkCooldown')
        self.addCleanup(patcher.stop)
        self.mock_markCooldown = patcher.start()
        self.mock_markCooldown.return_value = False

        patcher = patch(library.__name__ + '.processRandomQuote')
        self.addCleanup(patcher.stop)
        self.mock_randomQuote = patcher.start()
        self.mock_randomQuote.return_value = False

        patcher = patch(library.__name__ + '.processQuoteId')
        self.addCleanup(patcher.stop)
        self.mock_quoteId = patcher.start()
        self.mock_quoteId.return_value = False

        patcher = patch(library.__name__ + '.processRandomQuoteSearch')
        self.addCleanup(patcher.stop)
        self.mock_quoteSearch = patcher.start()
        self.mock_quoteSearch.return_value = False

    async def test_no_feature(self):
        self.features.clear()
        self.assertIs(await channel.commandQuote(self.args), False)
        self.assertFalse(self.mock_inCooldown.called)
        self.assertFalse(self.mock_markCooldown.called)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_cooldown(self):
        self.mock_inCooldown.return_value = True
        self.assertIs(await channel.commandQuote(self.args), False)
        self.assertTrue(self.mock_inCooldown.called)
        self.assertFalse(self.mock_markCooldown.called)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_random_quote_no_quote(self):
        self.assertIs(await channel.commandQuote(self.args), True)
        self.assertTrue(self.mock_inCooldown.called)
        self.assertFalse(self.mock_markCooldown.called)
        self.assertTrue(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_random_quote(self):
        self.mock_randomQuote.return_value = True
        self.assertIs(await channel.commandQuote(self.args), True)
        self.assertTrue(self.mock_inCooldown.called)
        self.assertTrue(self.mock_markCooldown.called)
        self.assertTrue(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_quote_id_no_quote(self):
        self.args = self.args._replace(message=Message('!quote 1'))
        self.assertIs(await channel.commandQuote(self.args), True)
        self.assertTrue(self.mock_inCooldown.called)
        self.assertFalse(self.mock_markCooldown.called)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertTrue(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_quote_id(self):
        self.args = self.args._replace(message=Message('!quote 1'))
        self.mock_quoteId.return_value = True
        self.assertIs(await channel.commandQuote(self.args), True)
        self.assertTrue(self.mock_inCooldown.called)
        self.assertTrue(self.mock_markCooldown.called)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertTrue(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_search_quote_no_quote(self):
        self.args = self.args._replace(message=Message('!quote a'))
        self.assertIs(await channel.commandQuote(self.args), True)
        self.assertTrue(self.mock_inCooldown.called)
        self.assertFalse(self.mock_markCooldown.called)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertTrue(self.mock_quoteSearch.called)

    async def test_search_quote(self):
        self.args = self.args._replace(message=Message('!quote a'))
        self.mock_quoteSearch.return_value = True
        self.assertIs(await channel.commandQuote(self.args), True)
        self.assertTrue(self.mock_inCooldown.called)
        self.assertTrue(self.mock_markCooldown.called)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertTrue(self.mock_quoteSearch.called)


class TestChannelQuoteAnyQuote(TestChannel):
    def setUp(self):
        super().setUp()

        self.permissionSet['manager'] = True

        patcher = patch(library.__name__ + '.processAnyRandomQuote')
        self.addCleanup(patcher.stop)
        self.mock_randomQuote = patcher.start()
        self.mock_randomQuote.return_value = False

        patcher = patch(library.__name__ + '.processAnyQuoteId')
        self.addCleanup(patcher.stop)
        self.mock_quoteId = patcher.start()
        self.mock_quoteId.return_value = False

        patcher = patch(library.__name__ + '.processAnyRandomQuoteSearch')
        self.addCleanup(patcher.stop)
        self.mock_quoteSearch = patcher.start()
        self.mock_quoteSearch.return_value = False

    async def test_permission(self):
        self.permissionSet['manager'] = False
        self.assertIs(await channel.commandAnyQuote(self.args), False)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_random_quote_no_quote(self):
        self.assertIs(await channel.commandAnyQuote(self.args), True)
        self.assertTrue(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_random_quote(self):
        self.mock_randomQuote.return_value = True
        self.assertIs(await channel.commandAnyQuote(self.args), True)
        self.assertTrue(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_quote_id_no_quote(self):
        self.args = self.args._replace(message=Message('!anyquote 1'))
        self.assertIs(await channel.commandAnyQuote(self.args), True)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertTrue(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_quote_id(self):
        self.args = self.args._replace(message=Message('!anyquote 1'))
        self.mock_quoteId.return_value = True
        self.assertIs(await channel.commandAnyQuote(self.args), True)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertTrue(self.mock_quoteId.called)
        self.assertFalse(self.mock_quoteSearch.called)

    async def test_search_quote_no_quote(self):
        self.args = self.args._replace(message=Message('!anyquote a'))
        self.assertIs(await channel.commandAnyQuote(self.args), True)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertTrue(self.mock_quoteSearch.called)

    async def test_search_quote(self):
        self.args = self.args._replace(message=Message('!anyquote a'))
        self.mock_quoteSearch.return_value = True
        self.assertIs(await channel.commandAnyQuote(self.args), True)
        self.assertFalse(self.mock_randomQuote.called)
        self.assertFalse(self.mock_quoteId.called)
        self.assertTrue(self.mock_quoteSearch.called)


class TestChannelQuoteQuotes(TestChannel):
    def setUp(self):
        super().setUp()

        self.features.append('quotes')

        patcher = patch(library.__name__ + '.handleQuoteList')
        self.addCleanup(patcher.stop)
        self.mock_list = patcher.start()
        self.mock_list.return_value = True

        patcher = patch(library.__name__ + '.handleAddQuote')
        self.addCleanup(patcher.stop)
        self.mock_add = patcher.start()
        self.mock_add.return_value = True

        patcher = patch(library.__name__ + '.handleEditQuote')
        self.addCleanup(patcher.stop)
        self.mock_edit = patcher.start()
        self.mock_edit.return_value = True

        patcher = patch(library.__name__ + '.handleDeleteQuote')
        self.addCleanup(patcher.stop)
        self.mock_delete = patcher.start()
        self.mock_delete.return_value = True

        patcher = patch(library.__name__ + '.handleCopyQuote')
        self.addCleanup(patcher.stop)
        self.mock_copy = patcher.start()
        self.mock_copy.return_value = True

        patcher = patch(library.__name__ + '.handleTagQuote')
        self.addCleanup(patcher.stop)
        self.mock_tag = patcher.start()
        self.mock_tag.return_value = True

        patcher = patch(library.__name__ + '.handleListQuoteIds')
        self.addCleanup(patcher.stop)
        self.mock_ids = patcher.start()
        self.mock_ids.return_value = True

    async def test_no_feature(self):
        self.features.clear()
        self.assertIs(await channel.commandQuotes(self.args), False)
        self.assertFalse(self.mock_list.called)
        self.assertFalse(self.mock_add.called)
        self.assertFalse(self.mock_edit.called)
        self.assertFalse(self.mock_delete.called)
        self.assertFalse(self.mock_copy.called)
        self.assertFalse(self.mock_tag.called)
        self.assertFalse(self.mock_ids.called)

    async def test_list(self):
        self.assertIs(await channel.commandQuotes(self.args), True)
        self.assertTrue(self.mock_list.called)
        self.assertFalse(self.mock_add.called)
        self.assertFalse(self.mock_edit.called)
        self.assertFalse(self.mock_delete.called)
        self.assertFalse(self.mock_copy.called)
        self.assertFalse(self.mock_tag.called)
        self.assertFalse(self.mock_ids.called)

    async def test_add(self):
        self.args = self.args._replace(message=Message('!quotes add'))
        self.assertIs(await channel.commandQuotes(self.args), True)
        self.assertFalse(self.mock_list.called)
        self.assertTrue(self.mock_add.called)
        self.assertFalse(self.mock_edit.called)
        self.assertFalse(self.mock_delete.called)
        self.assertFalse(self.mock_copy.called)
        self.assertFalse(self.mock_tag.called)
        self.assertFalse(self.mock_ids.called)

    async def test_edit(self):
        self.args = self.args._replace(message=Message('!quotes edit'))
        self.assertIs(await channel.commandQuotes(self.args), True)
        self.assertFalse(self.mock_list.called)
        self.assertFalse(self.mock_add.called)
        self.assertTrue(self.mock_edit.called)
        self.assertFalse(self.mock_delete.called)
        self.assertFalse(self.mock_copy.called)
        self.assertFalse(self.mock_tag.called)
        self.assertFalse(self.mock_ids.called)

    async def test_delete(self):
        self.args = self.args._replace(message=Message('!quotes delete'))
        self.assertIs(await channel.commandQuotes(self.args), True)
        self.assertFalse(self.mock_list.called)
        self.assertFalse(self.mock_add.called)
        self.assertFalse(self.mock_edit.called)
        self.assertTrue(self.mock_delete.called)
        self.assertFalse(self.mock_copy.called)
        self.assertFalse(self.mock_tag.called)
        self.assertFalse(self.mock_ids.called)

    async def test_copy(self):
        self.args = self.args._replace(message=Message('!quotes copy'))
        self.assertIs(await channel.commandQuotes(self.args), True)
        self.assertFalse(self.mock_list.called)
        self.assertFalse(self.mock_add.called)
        self.assertFalse(self.mock_edit.called)
        self.assertFalse(self.mock_delete.called)
        self.assertTrue(self.mock_copy.called)
        self.assertFalse(self.mock_tag.called)
        self.assertFalse(self.mock_ids.called)

    async def test_tag(self):
        self.args = self.args._replace(message=Message('!quotes tag'))
        self.assertIs(await channel.commandQuotes(self.args), True)
        self.assertFalse(self.mock_list.called)
        self.assertFalse(self.mock_add.called)
        self.assertFalse(self.mock_edit.called)
        self.assertFalse(self.mock_delete.called)
        self.assertFalse(self.mock_copy.called)
        self.assertTrue(self.mock_tag.called)
        self.assertFalse(self.mock_ids.called)

    async def test_id(self):
        self.args = self.args._replace(message=Message('!quotes id'))
        self.assertIs(await channel.commandQuotes(self.args), True)
        self.assertFalse(self.mock_list.called)
        self.assertFalse(self.mock_add.called)
        self.assertFalse(self.mock_edit.called)
        self.assertFalse(self.mock_delete.called)
        self.assertFalse(self.mock_copy.called)
        self.assertFalse(self.mock_tag.called)
        self.assertTrue(self.mock_ids.called)
