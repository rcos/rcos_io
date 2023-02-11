from django.urls import path

from portal.views.admin import (
    import_google_form_projects,
    import_submitty_enrollments,
    import_submitty_teams,
)
from portal.views.small_groups import SmallGroupDetailView, SmallGroupIndexView

from .views.auth import (
    discord_flow_callback,
    github_flow_callback,
    impersonate,
    profile,
    start_discord_flow,
    start_github_flow,
    unlink_discord,
    unlink_github,
)
from .views.index import HandbookView, IndexView
from .views.meetings import (
    MeetingDetailView,
    MeetingIndexView,
    SubmitAttendanceFormView,
    manually_add_or_verify_attendance,
    meetings_api,
    user_attendance,
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

    # Auth Routes
    path("profile", profile, name="profile"),
    path("auth/impersonate", impersonate, name="impersonate"),
    path("auth/discord", start_discord_flow, name="discord_flow"),
    path(
        "auth/discord/callback",
        discord_flow_callback,
        name="discord_flow_callback",
    ),
    path("auth/discord/unlink", unlink_discord, name="unlink_discord"),
    path("auth/github", start_github_flow, name="github_flow"),
    path("auth/github/callback", github_flow_callback, name="link_github_callback"),
    path("auth/github/unlink", unlink_github, name="unlink_github"),
    
    # User Routes
    path("users/", UserIndexView.as_view(), name="users_index"),
    path("users/enroll/", enroll_user, name="users_enroll"),
    path("users/<int:pk>", UserDetailView.as_view(), name="users_detail"),
    path("users/<int:pk>/attendance", user_attendance, name="user_attendance"),
    
    # Project Routes
    path(
        "projects/",
        ProjectIndexView.as_view(),
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

    # Meeting Routes
    path("meetings/", MeetingIndexView.as_view(), name="meetings_index"),
    path("attend", SubmitAttendanceFormView.as_view(), name="submit_attendance"),
    path(
        "meetings/attendance/verify",
        manually_add_or_verify_attendance,
        name="verify_attendance",
    ),
    path("meetings/<int:pk>", MeetingDetailView.as_view(), name="meetings_detail"),
    path("api/meetings", meetings_api, name="meetings_api"),
    
    # Small Group Routes
    path(
        "small_groups/",
        SmallGroupIndexView.as_view(),
        name="small_groups_index",
    ),
    path(
        "small_groups/<int:pk>",
        SmallGroupDetailView.as_view(),
        name="small_groups_detail",
    ),

    # Admin Routes
    path(
        "admin/import/enrollments",
        import_submitty_enrollments,
        name="import_enrollments",
    ),
    path(
        "admin/import/teams",
        import_submitty_teams,
        name="import_teams",
    ),
    path(
        "admin/import/projects",
        import_google_form_projects,
        name="import_projects",
    ),
]
