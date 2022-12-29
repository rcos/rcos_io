from django.urls import path

from portal.views.admin import upload_submitty_data

from .views.index import IndexView
from .views.meetings import MeetingIndexView, MeetingDetailView, meetings_api
from .views.users import UserIndexView, UserDetailView
from .views.projects import ProjectDetailView, ProjectIndexView
from .views.auth import start_discord_link, discord_link_callback

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("auth/link/discord", start_discord_link, name="link_discord"),
    path(
        "auth/link/discord/callback",
        discord_link_callback,
        name="link_discord_callback",
    ),
    # path("/auth/link/github", name="link_github")
    # path("/auth/link/github/callback", name="link_github_callback")
    path("users/", UserIndexView.as_view(), name="users_index"),
    path("users/<int:pk>", UserDetailView.as_view(), name="users_detail"),
    path("projects/", ProjectIndexView.as_view(), name="projects_index"),
    path("projects/<int:pk>", ProjectDetailView.as_view(), name="projects_detail"),
    path("meetings/", MeetingIndexView.as_view(), name="meetings_index"),
    path("api/meetings", meetings_api, name="meetings_api"),
    path("meetings/<int:pk>", MeetingDetailView.as_view(), name="meetings_detail"),
    path("admin/upload", upload_submitty_data, name="admin_upload")
]
