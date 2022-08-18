import asyncio
import cachetools
import logging
import pathlib
import time

from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.util.config import load_config
from chia.util.default_root import DEFAULT_ROOT_PATH
from chia.util.ints import uint16, uint64
from chiabot.plugin import PluginBase
from collections import defaultdict

logger = logging.getLogger('faucet')


class Faucet(PluginBase):

    NAME = 'faucet'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wallet_rpc_client = None
        self.addresses = defaultdict(int)
        self.authors = defaultdict(int)
        self.ttl = cachetools.TTLCache(
            self.config['faucet'].get('transactions_per_time_target', 100) * 2,
            self.config['faucet'].get('time_target', 86400),
        )

    async def on_ready(self, client):
        wallet_ssl_dir = self.config['faucet'].get('wallet_ssl_dir')
        wallet_hostname = self.config['faucet'].get('wallet_hostname') or 'localhost'
        wallet_port = self.config['faucet'].get('wallet_port') or 9256
        logger.info('Logging in into wallet')
        try:
            if wallet_ssl_dir:
                self.wallet_rpc_client = await WalletRpcClient.create(
                    wallet_hostname,
                    uint16(wallet_port),
                    pathlib.Path(wallet_ssl_dir),
                    {
                        'private_ssl_ca': {
                            'crt': 'private_ca.crt',
                            'key': 'private_ca.key',
                        },
                        'daemon_ssl': {
                            'private_crt': 'private_daemon.crt',
                            'private_key': 'private_daemon.key',
                        },
                    },
                )
            else:
                config = load_config(DEFAULT_ROOT_PATH, "config.yaml")
                self.wallet_rpc_client = await WalletRpcClient.create(
                    wallet_hostname, uint16(wallet_port), DEFAULT_ROOT_PATH, config
                )
        except Exception:
            logger.error('Failed to log in to wallet', exc_info=True)
        else:
            asyncio.ensure_future(self._log_in_loop())

    async def _log_in_loop(self):
        while True:
            try:
                res = await self.wallet_rpc_client.log_in(
                    fingerprint=self.config['faucet']['wallet_fingerprint'],
                )
                if not res["success"]:
                    logger.error(
                        'Error logging in: %s. Make sure your fingerprint is correct.', res['error']
                    )
            except Exception:
                logger.error('Failed to log in and skip for faucet wallet', exc_info=True)
            await asyncio.sleep(60)

    async def on_message(self, client, message):
        channel_id = self.config['faucet'].get('channel_id')
        if channel_id is not None and message.channel.id != channel_id:
            return
        if not message.content.startswith('.faucet '):
            return
        try:
            addr = message.content.split('.faucet ', 1)[-1].strip()
            if self.addresses[addr] > time.time() - self.config['faucet'].get(
                'addresses_time_target', 86400
            ):
                await message.channel.send('Mojo has already been sent to that address.')
            elif self.authors[message.author.id] > time.time() - self.config['faucet'].get(
                'authors_time_target', 86400
            ):
                await message.channel.send('Exceeded the amount of mojos in the last 24 hours.')
            elif len(self.ttl) >= self.config['faucet'].get('transactions_per_time_target', 100):
                await message.channel.send('Exceeded the amount of mojos in the last 24 hours.')
            else:
                mojos = self.config['faucet'].get('mojos', 1)
                transaction = await self.wallet_rpc_client.send_transaction(
                    self.config['faucet']['wallet_id'], mojos, addr, fee=uint64(1),
                )
                await message.channel.send(f'{mojos} Mojos sent! Transaction {transaction.name}')
                self.addresses[addr] = time.time()
                self.authors[message.author.id] = time.time()
                self.ttl[time.time()] = addr
        except ValueError as e:
            await message.channel.send(f'Failed to send: {e.args[0]["error"]}')
