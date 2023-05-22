"""Views relating to the administration of the RCOS Discord server."""

import time
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.urls import reverse

from portal.services import discord
from portal.views.admin import is_admin

from portal import tasks


@method_decorator(login_required, name="dispatch")
@method_decorator(user_passes_test(is_admin), name="dispatch")
class DiscordAdminIndex(TemplateView):
    """"""

    template_name = "portal/discord/index.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        # Fetch all channels from server
        channels = discord.get_server_channels()

        # Build hierarchy of channels in the following format:
        # (id, name): [child channels]
        categories = {}
        for channel in [
            c for c in channels if c["type"] == discord.CATEGORY_CHANNEL_TYPE
        ]:
            key = (channel["id"], channel["name"] if "name" in channel else "")
            categories[key] = [
                c
                for c in channels
                if "parent_id" in c and c["parent_id"] == channel["id"]
            ]
        categories[(None, "No category")] = [
            c
            for c in channels
            if "parent_id" not in c
            or c["parent_id"] is None
            and c["type"] != discord.CATEGORY_CHANNEL_TYPE
        ]

        data["categories"] = categories.items()

        return data


@login_required
@user_passes_test(is_admin)
def delete_discord_channels(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        channel_ids = [
            channel_id
            for channel_id in request.POST.getlist("channelID", [])
            if channel_id != "None"
        ]

        # TODO: run some checks about these channels

        # Kick off a task to delete these channels
        tasks.delete_discord_channels.delay(channel_ids)
        messages.success(request, "Deleting the Discord channels in the background...")

    return redirect(reverse("discord_admin_index"))
