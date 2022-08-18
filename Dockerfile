FROM debian:stable-slim

# Identify the maintainer of an image
LABEL maintainer="contact@openchia.io"

# Update the image to the latest packages
RUN apt-get update && apt-get upgrade -y

RUN apt-get install python3-virtualenv python3-yaml python3-aiohttp git vim procps net-tools iputils-ping -y

EXPOSE 8088

RUN mkdir -p /root/bot

WORKDIR /root/bot

COPY ./requirements.txt .
RUN virtualenv -p python3 venv
RUN ./venv/bin/pip install -r requirements.txt

COPY ./chiabot /root/bot/chiabot/

COPY ./docker/start.sh /root/

CMD ["bash", "/root/start.sh"]
