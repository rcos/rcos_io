from celery import shared_task

from portal.services import discord


@shared_task
def send_discord_message():
    discord.send_message("796073787316895814", {"content": "YES! IT works!!!"})
