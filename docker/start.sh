#!/bin/bash
set -e

trap "killall python" TERM

cd /root/bot
exec ./venv/bin/python -m chiabot.main \
	-p openchia_stats faucet \
	-c /data/bot-config.yaml
