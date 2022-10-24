import aiohttp
import asyncio
import humanize
import itertools
import logging

from chiabot.plugin import PluginBase

logger = logging.getLogger('openchia_stats')


class OpenChiaStats(PluginBase):

    NAME = 'openchia_stats'

    async def on_ready(self, client):
        asyncio.ensure_future(self.loop(client))

    async def loop(self, client):
        for i in itertools.count():
            try:
                await self.get_stats(client, i)
            except Exception:
                logger.error('Exception getting stats', exc_info=True)
            await asyncio.sleep(self.config['openchia_stats']['interval'])

    async def get_stats(self, client, i):
        async with aiohttp.request('GET', 'https://openchia.io/api/v1.0/stats') as r:
            if r.status != 200:
                return
            stats = await r.json()

            guild = await client.fetch_guild(865233670938689537)
            me = await guild.fetch_member(client.user.id)

            i = i % 6
            if i == 0:
                await me.edit(nick=f'Farmers: {stats["farmers_active"]}')
            elif i == 1:
                await me.edit(nick=f'Pool size: {humanize.naturalsize(stats["pool_space"], True)}')
            elif i == 2:
                await me.edit(nick=f'Netspace: {humanize.naturalsize(stats["blockchain_space"], True)}')
            elif i == 3:
                await me.edit(nick=f'Height: {stats["blockchain_height"]}')
            elif i == 4:
                await me.edit(nick=f'Price: ${stats["xch_current_price"]["usd"]}')
            elif i == 5:
                await me.edit(nick=f'Dust Storm: {"yes" if stats["blockchain_duststorm"] else "no"}')
