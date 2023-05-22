import time
from typing import List
from celery import shared_task
from requests import HTTPError

from portal.services import discord

@shared_task
def delete_discord_channels(channel_ids: List[str]):
    for channel_id in channel_ids:
        try:
            discord.delete_channel(channel_id)
        except HTTPError as e:
            print(e, e.response)
        time.sleep(2)
