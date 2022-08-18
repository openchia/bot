import argparse
import discord
import logging
import logging.config
import yaml

from .client import ChiaBotClient
from .plugin import Plugins


def configure_logging():
    logging.root.setLevel(logging.INFO)

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "loggers": {
            "": {
                "handlers": ["console"],
            },
        },
        "handlers": {
            "console": {
                "level": "INFO",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "console",
            },
        },
        "formatters": {
            "console": {
                "()": "colorlog.ColoredFormatter",
                "format": "[%(asctime)s] (%(log_color)s%(levelname)-8s%(reset)s) %(name)s.%(funcName)s():%(lineno)d - %(message)s",
            },
        }
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', required=True)
    parser.add_argument('-p', '--plugin', nargs='+')
    args = parser.parse_args()

    configure_logging()

    with open(args.config, 'r') as f:
        config = yaml.safe_load(f.read())

    plugins = Plugins(config, includes=args.plugin or None)

    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    client = ChiaBotClient(plugins=plugins, intents=intents)

    client.run(config['token'])


if __name__ == '__main__':
    main()
