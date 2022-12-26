from django.shortcuts import redirect
from django.core.exceptions import BadRequest
from portal.services import discord
from rcos_io import settings
from requests import HTTPError
from django.contrib.auth.decorators import login_required


@login_required
def start_discord_link(request):
    return redirect(discord.DISCORD_OAUTH2_URL)


@login_required
def discord_link_callback(request):
    code = request.GET.get("code")
    if not code:
        raise BadRequest

    try:
        discord_user_tokens = discord.get_tokens(code)
        discord_access_token = discord_user_tokens["access_token"]
        discord_user_info = discord.get_user_info(discord_access_token)
    except HTTPError as error:
        return error

    discord_user_id = discord_user_info["id"]

    request.user.discord_user_id = discord_user_id
    request.user.save()

    return redirect("/")
