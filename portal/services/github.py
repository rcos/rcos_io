from typing import TypedDict

import requests
from django.conf import settings
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

GITHUB_AUTH_URL = (
    "https://github.com/login/oauth/authorize"
    f"?client_id={settings.GITHUB_OAUTH_APP_CLIENT_ID}&redirect_uri={settings.GITHUB_OAUTH_APP_REDIRECT_URL}"
)


class GitHubTokens(TypedDict):
    """
    https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps#response
    """

    access_token: str
    scope: str
    token_type: int


def get_tokens(code: str) -> GitHubTokens:
    """
    Given an authorization code, request an access token for a GitHub user.
    Returns:
        GitHubTokens
    Raises:
        HTTPError on failed request
    See https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps
    """
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": settings.GITHUB_OAUTH_APP_CLIENT_ID,
            "client_secret": settings.GITHUB_OAUTH_APP_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GITHUB_OAUTH_APP_REDIRECT_URL,
        },
        headers={"Accept": "application/json"},
        timeout=3,
    )
    response.raise_for_status()
    # https://requests.readthedocs.io/en/latest/user/quickstart/#response-status-codes
    # throws HTTPError for 4XX or 5XX
    tokens = response.json()
    return tokens


def get_user_username(client: Client) -> str:
    query = gql(
        """
        {
            viewer {
                login
            }
        }
        """
    )

    result = client.execute(query)
    return result["viewer"]["login"]


def client_factory(token: str = settings.GITHUB_API_TOKEN):
    """
    Creates a new GQL client pointing to the Hasura API.
    Instead of using one client across the app, one client should be made per request
    to avoid threading errors.
    Returns:
        new GQL client
    """
    transport = RequestsHTTPTransport(
        url="https://api.github.com/graphql",
        verify=True,
        retries=3,
        headers={"Authorization": f"bearer {token}"},
    )
    return Client(transport=transport)


def get_repository_details(client: Client, repo_url: str):
    owner, name = repo_url.split("/")[-2:]
    query = gql(
        """
        query RepoDetails($owner: String!, $name: String!) {
            repository(owner: $owner, name: $name) {
                owner {
                    login
                }
                name
                url
                description
                forkCount
                stargazerCount
                primaryLanguage {
                    name
                    color
                }
                defaultBranchRef {
                target {
                    ... on Commit {
                    history(first: 5) {
                        nodes {
                        url
                        author {
                            name
                            user {
                                login
                            }
                            avatarUrl
                        }
                        authoredDate
                        additions
                        deletions
                        messageHeadline
                        messageBody
                        }
                    }
                    }
                }
                }
                readme: object(expression: "main:README.md") {
                ... on Blob {
                    text
                }
                }
                license: object(expression: "main:LICENSE") {
                ... on Blob {
                    text
                }
                }
            }
        }
        """
    )

    result = client.execute(query, variable_values={"owner": owner, "name": name})
    return result
