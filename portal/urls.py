from django.urls import path
from django.views.decorators.cache import cache_page

from portal.views.admin import import_google_form_projects, import_submitty_enrollments
from portal.views.small_groups import SmallGroupDetailView, SmallGroupIndexView

from .views.auth import (
    change_email,
    discord_link_callback,
    github_link_callback,
    impersonate,
    profile,
    start_discord_link,
    start_github_link,
    unlink_discord,
    unlink_github,
    verify_change_email,
)
from .views.index import HandbookView, IndexView
from .views.meetings import (
    MeetingDetailView,
    MeetingIndexView,
    SubmitAttendanceFormView,
    manually_add_or_verify_attendance,
    meetings_api,
)
from .views.projects import (
    ProjectAddPitch,
    ProjectDetailView,
    ProjectIndexView,
    ProjectProposeView,
)
from .views.users import UserDetailView, UserIndexView, enroll_user

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("handbook", HandbookView.as_view(), name="handbook"),
    path("profile", profile, name="profile"),
    path("auth/change_email", change_email, name="change_email"),
    path("auth/change_email/verify", verify_change_email, name="verify_change_email"),
    path("auth/impersonate", impersonate, name="impersonate"),
    path("auth/link/discord", start_discord_link, name="link_discord"),
    path(
        "auth/link/discord/callback",
        discord_link_callback,
        name="link_discord_callback",
    ),
    path("auth/unlink/discord", unlink_discord, name="unlink_discord"),
    path("auth/link/github", start_github_link, name="link_github"),
    path(
        "auth/link/github/callback", github_link_callback, name="link_github_callback"
    ),
    path("auth/unlink/github", unlink_github, name="unlink_github"),
    path("users/", cache_page(60 * 15)(UserIndexView.as_view()), name="users_index"),
    path("users/enroll/", enroll_user, name="users_enroll"),
    path("users/<int:pk>", UserDetailView.as_view(), name="users_detail"),
    path(
        "projects/",
        cache_page(60 * 15)(ProjectIndexView.as_view()),
        name="projects_index",
    ),
    path("projects/propose/", ProjectProposeView.as_view(), name="projects_propose"),
    path("projects/<int:pk>", ProjectDetailView.as_view(), name="projects_detail"),
    path("projects/<slug:slug>", ProjectDetailView.as_view(), name="projects_detail"),
    path(
        "projects/<slug:slug>/pitch",
        ProjectAddPitch.as_view(),
        name="projects_add_pitch",
    ),
    path("meetings/", MeetingIndexView.as_view(), name="meetings_index"),
    path("attend", SubmitAttendanceFormView.as_view(), name="submit_attendance"),
    path(
        "meetings/attendance/verify",
        manually_add_or_verify_attendance,
        name="verify_attendance",
    ),
    path("meetings/<int:pk>", MeetingDetailView.as_view(), name="meetings_detail"),
    path("api/meetings", meetings_api, name="meetings_api"),
    path(
        "small_groups/",
        cache_page(60 * 15)(SmallGroupIndexView.as_view()),
        name="small_groups_index",
    ),
    path(
        "small_groups/<int:pk>",
        SmallGroupDetailView.as_view(),
        name="small_groups_detail",
    ),
    path(
        "admin/import/submitty",
        import_submitty_enrollments,
        name="admin_import_submitty",
    ),
    path(
        "admin/import/projects",
        import_google_form_projects,
        name="admin_import_projects",
    ),
]
