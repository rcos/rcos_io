from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import BadRequest
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from requests import HTTPError

from portal.forms import ChangeEmailForm, UserProfileForm
from portal.models import User
from portal.services import discord, github


@login_required
def profile(request):
    if request.method == "POST":
        form = UserProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            messages.success(request, "Your profile was updated.")
            form.save()
            return redirect(reverse("profile"))
    else:
        form = UserProfileForm(instance=request.user)

    return render(
        request,
        "portal/auth/profile.html",
        {"form": form, "change_email_form": ChangeEmailForm()},
    )


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

        try:
            discord.add_user_to_server(discord_access_token, settings.DISCORD_SERVER_ID)
            messages.success(request, "Added you to the RCOS Discord server!")
        except:
            messages.warning(request, "Failed to add you to the RCOS Discord server...")

        try:
            discord.add_role_to_member(
                discord_user_info["id"], settings.DISCORD_VERIFIED_ROLE_ID
            )
        except Exception as e:
            print(e)

        try:
            discord.set_member_nickname(
                discord_user_info["id"], request.user.display_name
            )
        except:
            messages.warning(
                request,
                "Failed to set your nickname and/or role on the Discord server...",
            )

    except HTTPError as error:
        messages.error(request, "Yikes! Failed to link your Discord.")
        return redirect(reverse("profile"))

    discord_user_id = discord_user_info["id"]

    request.user.discord_user_id = discord_user_id
    request.user.save()

    messages.success(
        request,
        f"Successfully linked Discord account @{discord_user_info['username']}#{discord_user_info['discriminator']} to your profile.",
    )
    return redirect(reverse("profile"))


@login_required
def start_github_link(request):
    return redirect(github.GITHUB_AUTH_URL)


@login_required
def github_link_callback(request):
    code = request.GET.get("code")
    if not code:
        raise BadRequest

    try:
        github_user_tokens = github.get_tokens(code)
        github_access_token = github_user_tokens["access_token"]
        client = github.client_factory(github_access_token)
        github_username = github.get_user_username(client)
    except HTTPError as error:
        messages.error(request, "Yikes! Failed to link your GitHub.")
        return redirect(reverse("profile"))

    request.user.github_username = github_username
    request.user.save()

    messages.success(
        request,
        f"Successfully linked GitHub account @{github_username} to your profile.",
    )
    return redirect(reverse("profile"))


@login_required
def change_email(request):
    if request.method == "POST":
        form = ChangeEmailForm(request.POST)

        if form.is_valid():
            new_email = form.cleaned_data["new_email"]
            verification_code = "abcd"
            request.session["email_change"] = {
                "new_email": new_email,
                "verification_code": verification_code,
                "expires_at": (
                    timezone.now() + timezone.timedelta(minutes=1)
                ).isoformat(),
            }
            send_mail(
                subject="Verify email address change",
                message=f"""Hi {request.user.first_name or 'RCOS member'}, we received a request to change your primary email to this account.
                If you did not make such a request, please ignore this email. Otherwise, click the link below to confirm the change. Once confirmed, you will only be able to login with this email address and not the original.

                {settings.PUBLIC_BASE_URL}{reverse("verify_change_email")}?verification_code={verification_code}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[new_email],
                fail_silently=False,
            )

            messages.info(
                request,
                f"Check {new_email} for a verification email to confirm your email change.",
            )
        else:
            messages.warning(
                request,
                "Unable to submit your email change request. That email might already be in use or invalid.",
            )

    return redirect(reverse("profile"))


@login_required
def verify_change_email(request):
    try:
        verification_code = request.GET["verification_code"]
        email_change = request.session.pop("email_change")
        if timezone.datetime.fromisoformat(email_change["expires_at"]) < timezone.now():
            messages.error(
                request, "Your email change request expired. Please try again."
            )
        elif verification_code == email_change["verification_code"]:
            request.user.email = email_change["new_email"]
            request.user.save()
            messages.success(
                request,
                f"You've confirmed your email change to {request.user.email}. Please use this email to login in the future.",
            )
            return redirect(reverse("profile"))
    except:
        messages.error(request, "Could not confirm your email address change.")

    return redirect(reverse("profile"))
