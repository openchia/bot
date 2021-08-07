import discord
import logging

logger = logging.getLogger('client')


class ChiaBotClient(discord.Client):

    def __init__(self, *args, plugins=None, **kwargs):
        self.plugins = plugins
        super().__init__(*args, **kwargs)

    async def on_ready(self):
        logger.info(f'We have logged in as {self.user}')
        await self.plugins.on_ready(self)

    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')
