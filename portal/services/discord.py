from typing import Any, NotRequired, TypedDict, cast

import requests
from django.conf import settings

DISCORD_VERSION_NUMBER = "10"
DISCORD_API_ENDPOINT = f"https://discord.com/api/v{DISCORD_VERSION_NUMBER}"

DISCORD_OAUTH2_URL = (
    "https://discord.com/api/oauth2/authorize"
    f"?client_id={settings.DISCORD_CLIENT_ID}&redirect_uri={settings.DISCORD_REDIRECT_URL}"
    "&response_type=code&scope=identify%20guilds.join&prompt=consent"
)

HEADERS = {
    "Authorization": f"Bot {settings.DISCORD_BOT_TOKEN}",
}
"""
Base headers to send along with Discord API requests.
Most important is the `Authorization` header with the Discord bot's secret token
which authenticates requests and gives us permission to do things as the bot.
"""


class DiscordTokens(TypedDict):
    """https://discord.com/developers/docs/topics/oauth2#authorization-code-grant-access-token-response."""

    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str


def get_tokens(code: str) -> DiscordTokens:
    """Given an authorization code
    - requests the access and refresh tokens for a Discord user
    See
    https://discord.com/developers/docs/topics/oauth2#authorization-code-grant-access-token-exchange-example
    Args:
        code: the authorization code returned from Discord
    Returns:
        a DiscordTokens dict containing access token, expiration, etc.

    Raises
    ------
        HTTPError: if HTTP request fails.
    """
    response = requests.post(
        f"{DISCORD_API_ENDPOINT}/oauth2/token",
        data={
            "client_id": settings.DISCORD_CLIENT_ID,
            "client_secret": settings.DISCORD_CLIENT_SECRET,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.DISCORD_REDIRECT_URL,
            "scope": "identity guilds.join",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=3,
    )
    response.raise_for_status()
    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    tokens = response.json()
    return tokens


class DiscordUser(TypedDict):
    """See https://discord.com/developers/docs/resources/user#user-object."""

    id: str
    username: str
    discriminator: str
    avatar: NotRequired[str]
    banner: NotRequired[str]
    accent_color: NotRequired[str]


def get_user_info(access_token: str) -> DiscordUser:
    """Given an access token get a Discord user's info including
    - id
    - username
    - discriminator
    - avatar url
    - etc.

    Args:
    ----
        access_token: Discord access token for a user
    Raises:
        HTTPError on request failure
    See:
    https://discord.com/developers/docs/topics/oauth2#authorization-code-grant-access-token-exchange-example.
    """
    response = requests.get(
        f"{DISCORD_API_ENDPOINT}/users/@me",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        timeout=3,
    )
    response.raise_for_status()
    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    user = response.json()
    return user


def upsert_server_member(
    access_token: str,
    user_id: str,
    nickname: str | None = None,
    roles: list[str] | None = None,
):
    """Given a Discord user's id, add them to the RCOS server and/or update them with the given nickname and roles.

    Args:
    ----
        access_token: Discord user's access token
        user_id: Discord user's account ID
        nickname: nickname to give the member, must be <= 32 chars (optional)
        roles: list of Discord role IDs to assign the member (optional)

    Returns:
    -------
        joined_server: whether user was added to the server (false if already on server)
        updated_member: whether the member's Discord nickname and/or roles were updated
    Raises:
        HTTPError on failed request
    See https://discord.com/developers/docs/resources/guild#add-guild-member
    See https://discord.com/developers/docs/resources/guild#modify-guild-member.
    """
    data: dict[str, Any] = {
        "access_token": access_token,
    }

    if nickname is not None:
        data["nick"] = nickname

    response = requests.put(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/members/{user_id}",
        json=data,
        headers=HEADERS,
        timeout=3,
    )

    response.raise_for_status()

    joined_server = response.status_code == 201

    # Add roles
    for role in roles if roles else []:
        response = requests.put(
            f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/members/{user_id}/roles/{role}",
            json={"roles": roles},
            headers=HEADERS,
            timeout=3,
        )

    return joined_server


def get_user(user_id: str) -> DiscordUser | None:
    """Given a Discord user's id, gets their user info.

    Args:
    ----
        user_id: Discord user's unique account ID
    Returns:
        DiscordUser
    Raises:
        HTTPError on failed request (e.g. not found)
    See https://discord.com/developers/docs/resources/user#get-user.
    """
    response = requests.get(
        f"{DISCORD_API_ENDPOINT}/users/{user_id}", headers=HEADERS, timeout=3
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()
    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    user = response.json()
    return user


def get_server_member(user_id: str) -> dict[str, Any] | None:
    """Given a Discord user's id, gets their user server member profile.

    Args:
    ----
        user_id: Discord user's unique account ID
    Returns:
        DiscordUser
    Raises:
        HTTPError on failed request (e.g. not found)
    See https://discord.com/developers/docs/resources/guild#get-guild-member.
    """
    response = requests.get(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/members/{user_id}",
        headers=HEADERS,
        timeout=3,
    )

    if response.status_code == 404:
        return None

    response.raise_for_status()

    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    user = response.json()
    return user


def create_user_dm_channel(user_id: str):
    """https://discord.com/developers/docs/resources/user#create-dm."""
    response = requests.post(
        f"{DISCORD_API_ENDPOINT}/users/@me/channels",
        json={
            "recipient_id": user_id,
        },
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    return cast(dict[str, Any], response.json())


def dm_user(dm_channel_id: str, message_content: str):
    """https://discord.com/developers/docs/resources/channel#create-message."""
    response = requests.post(
        f"{DISCORD_API_ENDPOINT}/channels/{dm_channel_id}/messages",
        json={"content": message_content},
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    return response.json()


TEXT_CHANNEL_TYPE = 0
VOICE_CHANNEL_TYPE = 2
CATEGORY_CHANNEL_TYPE = 4


class CreateServerChannelParams(TypedDict):
    name: str
    type: NotRequired[int]
    topic: NotRequired[str]
    position: NotRequired[int]
    parent_id: NotRequired[str]


def create_server_channel(params: CreateServerChannelParams):
    response = requests.post(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/channels",
        headers=HEADERS,
        timeout=3,
        json=params,
    )

    response.raise_for_status()

    return cast(dict[str, Any], response.json())


class ModifyChannelParams(CreateServerChannelParams):
    name: NotRequired[str]


def modify_server_channel(channel_id: str, params: ModifyChannelParams):
    response = requests.patch(
        f"{DISCORD_API_ENDPOINT}/channels/{channel_id}",
        headers=HEADERS,
        timeout=3,
        json=params,
    )

    response.raise_for_status()

    return cast(dict[str, Any], response.json())


class SendMessageParams(TypedDict):
    content: str


def send_message(channel_id: str, params: SendMessageParams):
    response = requests.post(
        f"{DISCORD_API_ENDPOINT}/channels/{channel_id}/messages",
        headers=HEADERS,
        timeout=3,
        json=params,
    )

    response.raise_for_status()

    return cast(dict[str, Any], response.json())


class CreateRoleParams(TypedDict):
    name: NotRequired[str]
    permissions: NotRequired[str]
    color: NotRequired[int]
    hoist: NotRequired[bool]
    mentionable: NotRequired[bool]


def create_role(params: CreateRoleParams):
    response = requests.post(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/roles",
        headers=HEADERS,
        timeout=3,
        json=params,
    )

    response.raise_for_status()

    return cast(dict[str, Any], response.json())


def add_role_to_member(user_id: str, role_id: str):
    """Adds a role to a server member.

    Args:
    ----
        user_id: Discord user's unique account ID (same as member ID)
        role_id: ID of Discord role to add to member
    Raises:
        HTTPError on failed request (will not fail if role is already set)
    See https://discord.com/developers/docs/resources/guild#modify-guild-member.
    """
    response = requests.put(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}"
        f"/members/{user_id}/roles/{role_id}",
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    return response


def kick_user_from_server(user_id: str):
    """Given a Discord user's id, kicks them from the RCOS server.

    Args:
    ----
        user_id: Discord user's unique account ID
    Raises:
        HTTPError on failed request (e.g. missing permission to kick member)
    See https://discord.com/developers/docs/resources/guild#remove-guild-member.
    """
    response = requests.delete(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/members/{user_id}",
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    return response


def set_member_nickname(user_id: str, nickname: str):
    """Given a Discord user's id, sets their nickname on the server.

    Args:
    ----
        user_id: Discord user's unique account ID
        nickname: the nickname to give the user, must be <= 32 characters
    Raises:
        HTTPError on failed request
    See https://discord.com/developers/docs/resources/guild#modify-current-member.
    """
    response = requests.patch(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/members/{user_id}",
        json={"nick": nickname},
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    return response


class ServerScheduledEvent(TypedDict):
    id: str
    guild_id: str
    name: str
    description: NotRequired[str]
    scheduled_start_time: str
    scheduled_end_time: NotRequired[str]
    privacy_level: str
    status: str


def get_server_event(event_id: str) -> ServerScheduledEvent:
    """https://discord.com/developers/docs/resources/guild-scheduled-event#get-guild-scheduled-event."""
    response = requests.get(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/scheduled-events/{event_id}",
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    return cast(dict[str, Any], response.json())


def create_server_event(
    name: str,
    scheduled_start_time: str,
    scheduled_end_time: str,
    description: str,
    location: str | None,
) -> ServerScheduledEvent:
    """https://discord.com/developers/docs/resources/guild-scheduled-event#create-guild-scheduled-event."""
    response = requests.post(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/scheduled-events",
        json={
            "entity_metadata": {"location": location},
            "name": name,
            "description": description,
            "entity_type": 3,  # external event
            "scheduled_start_time": scheduled_start_time,
            "scheduled_end_time": scheduled_end_time,
            "privacy_level": 2,
        },
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    return response.json()


def update_server_event(
    event_id: str,
    name: str,
    scheduled_start_time: str,
    scheduled_end_time: str,
    description: str,
    location: str | None,
) -> ServerScheduledEvent:
    """https://discord.com/developers/docs/resources/guild-scheduled-event#create-guild-scheduled-event."""
    response = requests.patch(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/scheduled-events/{event_id}",
        json={
            "entity_metadata": {"location": location},
            "name": name,
            "description": description,
            "entity_type": 3,  # external event
            "scheduled_start_time": scheduled_start_time,
            "scheduled_end_time": scheduled_end_time,
            "privacy_level": 2,
        },
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    return response.json()


def delete_server_event(
    event_id: str,
):
    """https://discord.com/developers/docs/resources/guild-scheduled-event#delete-guild-scheduled-event."""
    response = requests.delete(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/scheduled-events/{event_id}",
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    return response.json()


class ServerChannel(TypedDict):
    """https://discord.com/developers/docs/resources/channel#channel-object-channel-structure."""

    id: str
    type: int
    name: NotRequired[str]
    topic: NotRequired[str]
    position: NotRequired[int]
    parent_id: NotRequired[str]


def get_server_channels():
    response = requests.get(
        f"{DISCORD_API_ENDPOINT}/guilds/{settings.DISCORD_SERVER_ID}/channels",
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    return cast(list[ServerChannel], response.json())


def delete_channel(channel_id: str):
    response = requests.delete(
        f"{DISCORD_API_ENDPOINT}/channels/{channel_id}",
        headers=HEADERS,
        timeout=3,
    )
    response.raise_for_status()
    return cast(ServerChannel, response.json())
