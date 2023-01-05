from django.urls import path

from portal.views.admin import import_submitty_data

from .views.index import HandbookView, IndexView
from .views.meetings import MeetingIndexView, MeetingDetailView, meetings_api
from .views.users import UserIndexView, UserDetailView, enroll_user
from .views.projects import ProjectProposeView, ProjectDetailView, ProjectIndexView
from .views.auth import (
    change_email,
    impersonate,
    profile,
    start_discord_link,
    discord_link_callback,
    verify_change_email,
)
from portal.views.small_groups import SmallGroupDetailView, SmallGroupIndexView

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("handbook", HandbookView.as_view(), name="handbook"),
    path("auth/profile", profile, name="profile"),
    path("auth/change_email", change_email, name="change_email"),
    path("auth/change_email/verify", verify_change_email, name="verify_change_email"),
    path("auth/impersonate", impersonate, name="impersonate"),
    path("auth/link/discord", start_discord_link, name="link_discord"),
    path(
        "auth/link/discord/callback",
        discord_link_callback,
        name="link_discord_callback",
    ),
    # path("/auth/link/github", name="link_github")
    # path("/auth/link/github/callback", name="link_github_callback")
    path("users/", UserIndexView.as_view(), name="users_index"),
    path("users/enroll/", enroll_user, name="users_enroll"),
    path("users/<int:pk>", UserDetailView.as_view(), name="users_detail"),
    path("projects/", ProjectIndexView.as_view(), name="projects_index"),
    path("projects/propose/", ProjectProposeView.as_view(), name="projects_propose"),
    path("projects/<int:pk>", ProjectDetailView.as_view(), name="projects_detail"),
    path("projects/<slug:slug>", ProjectDetailView.as_view(), name="projects_detail"),
    path("meetings/", MeetingIndexView.as_view(), name="meetings_index"),
    path("api/meetings", meetings_api, name="meetings_api"),
    path("meetings/<int:pk>", MeetingDetailView.as_view(), name="meetings_detail"),
    path("small_groups/", SmallGroupIndexView.as_view(), name="small_groups_index"),
    path(
        "small_groups/<int:pk>",
        SmallGroupDetailView.as_view(),
        name="small_groups_detail",
    ),
    path("admin/import", import_submitty_data, name="admin_import"),
]
