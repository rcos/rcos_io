import os
import time

from celery import shared_task
from django.db.models import Manager
from django.utils import timezone
from requests import HTTPError

from portal.models import Meeting
from portal.services import discord


@shared_task
def delete_discord_channels(channel_ids: list[str]):
    for channel_id in channel_ids:
        try:
            discord.delete_channel(channel_id)
        except HTTPError as e:
            print(e, e.response)
        time.sleep(2)

@shared_task
def meetings_alert():
    today = timezone.now().date()

    # Find meetings today
    todays_meetings: Manager[Meeting] = Meeting.objects.filter(start_date__date=today)

    for meeting in todays_meetings:
        if not meeting.presentation_url:
            # Meeting today is missing presentation URL, alert!
            discord.send_message(os.environ["DISCORD_ALERTS_CHANNEL_ID"], {
                "content": f"Meeting **{meeting}** does not have presentation slides added yet!"
            })
