from importlib.machinery import SourceFileLoader

import logging
import pathlib

logger = logging.getLogger('plugin')


class PluginBase(object):

    NAME = NotImplemented

    def __repr__(self):
        return f'Plugin<{self.NAME}>'

    def __init__(self, config):
        self.config = config


class Plugins(object):

    def __init__(self, config, includes=None):
        self.config = config
        self.includes = includes
        self.plugins = self.__load_plugins()
        logger.info('Loaded plugins: %r', self.plugins)

    def __load_plugins(self):
        path = pathlib.Path(__file__)
        path = path.parent / 'plugins'
        plugins = []
        for i in path.iterdir():
            if i.is_dir() or not i.name.endswith('.py'):
                continue

            mod = SourceFileLoader(i.name, str(i)).load_module()
            for j in dir(mod):

                attr = getattr(mod, j)
                try:
                    if not (issubclass(attr, PluginBase) and attr != PluginBase):
                        continue
                except TypeError:
                    continue

                if attr.NAME is NotImplemented:
                    attr.NAME = i.name.split('.')[0]

                if self.includes is None or attr.NAME in self.includes:
                    plugins.append(attr(self.config))

                break  # Only one plugin per file
        return plugins

    async def exec_plugin(self, client, name, args=None, kwargs=None):
        for p in self.plugins:
            try:
                if not hasattr(p, name):
                    continue
                await getattr(p, name)(client, *(args or []), **(kwargs or {}))
            except Exception:
                logger.error('Failed to run %s for %r', name, p, exc_info=True)

    async def on_ready(self, client):
        await self.exec_plugin(client, 'on_ready')

    async def on_message(self, client, message):
        await self.exec_plugin(client, 'on_message', [message])
