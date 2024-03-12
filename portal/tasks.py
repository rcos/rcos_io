import os
import time

from celery import shared_task
from django.db.models import Manager
from django.utils import timezone
from requests import HTTPError
from django.core.cache import cache

from portal.models import Meeting, Semester
from portal.services import discord, github

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

@shared_task
def get_commits():
    semester = Semester.objects.latest("start_date")
    for project in semester.projects.filter(is_approved=True).all():
        for repo in project.repositories.all():
            commits = {}
            result = github.get_repository_commits(github.client_factory(), repo.url, semester.start_date.strftime('%Y-%m-%dT%H:%M:%S.%f%z'))
            for branch in result["repository"]["refs"]["edges"]:
                for commit in branch["node"]["target"]["history"]["edges"]:
                    if (commit["node"]["committer"]["user"] != None):
                        commits[commit["node"]["commitUrl"]] = {
                            "committer": commit["node"]["committer"]["user"]["login"],
                            "additions": commit["node"]["additions"],
                            "deletions": commit["node"]["deletions"]
                        }
            cache.set(f"repo_commits_{repo.url}", commits, 60 * 60 * 24)