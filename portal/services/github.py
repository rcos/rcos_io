from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from django.conf import settings


def client_factory():
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
        headers={"Authorization": f"bearer {settings.GITHUB_API_TOKEN}"},
    )
    print(settings.GITHUB_API_TOKEN)
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
