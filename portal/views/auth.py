from django.shortcuts import redirect
from django.core.exceptions import BadRequest
from portal.forms import UserProfileForm
from portal.services import discord
from django.conf import settings
from portal.models import User
from requests import HTTPError
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render
from django.contrib import messages


@login_required
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            messages.success(request, "Your profile was updated.")
            form.save()
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, "portal/auth/profile.html", {"form": form})


def impersonate(request):
    if settings.DEBUG or request.user.is_superuser:
        email = request.POST["email"]
        user = User.objects.get(email=email)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")

    return redirect("/")


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


# def ChangeEmailView(FormView):
