from django.urls import path

from portal.views.admin import (
    import_google_form_projects,
    import_submitty_enrollments,
    import_submitty_teams,
)
from portal.views.discord import DiscordAdminIndex, delete_discord_channels
from portal.views.mentors import MentorApplicationView, mentor_applications_index
from portal.views.organizations import organizations_index
from portal.views.small_groups import SmallGroupIndexView, small_group_detail

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
from .views.index import IndexView, handbook
from .views.meetings import (
    MeetingDetailView,
    SubmitAttendanceFormView,
    export_meeting_attendance,
    manually_add_or_verify_attendance,
    meetings_api,
    meetings_index,
    user_attendance,
)
from .views.projects import (
    ProjectAddPitch,
    ProjectAddProposal,
    ProjectCreateView,
    ProjectIndexView,
    project_detail,
    project_lead_index,
)
from .views.users import UserIndexView, enroll_user, user_detail

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("handbook", handbook, name="handbook"),
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
    path("users/<int:pk>", user_detail, name="users_detail"),
    path("users/<int:pk>/enroll", enroll_user, name="users_enroll"),
    path("users/<int:pk>/attendance", user_attendance, name="user_attendance"),
    # Project Routes
    path(
        "projects/",
        ProjectIndexView.as_view(),
        name="projects_index",
    ),
    path("projects/lead/", project_lead_index, name="project_lead_index"),
    path("projects/new/", ProjectCreateView.as_view(), name="new_project"),
    path("projects/<slug:slug>", project_detail, name="projects_detail"),
    path(
        "projects/<slug:slug>/pitch",
        ProjectAddPitch.as_view(),
        name="projects_add_pitch",
    ),
    path(
        "projects/<slug:slug>/propose",
        ProjectAddProposal.as_view(),
        name="projects_add_proposal",
    ),
    # Meeting Routes
    path("meetings/", meetings_index, name="meetings_index"),
    path("attend", SubmitAttendanceFormView.as_view(), name="submit_attendance"),
    path(
        "meetings/attendance/verify",
        manually_add_or_verify_attendance,
        name="verify_attendance",
    ),
    path("meetings/<int:pk>", MeetingDetailView.as_view(), name="meetings_detail"),
    path(
        "meetings/<int:pk>/export",
        export_meeting_attendance,
        name="export_meeting_attendance",
    ),
    path("api/meetings", meetings_api, name="meetings_api"),
    # Mentor Routes
    path("mentors/applications", mentor_applications_index, name="mentor_applications"),
    path(
        "mentors/apply",
        MentorApplicationView.as_view(),
        name="mentors_apply",
    ),
    # Small Group Routes
    path(
        "small_groups/",
        SmallGroupIndexView.as_view(),
        name="small_groups_index",
    ),
    path(
        "small_groups/<int:pk>",
        small_group_detail,
        name="small_groups_detail",
    ),
    # Organization routes
    path("organizations/", organizations_index, name="organizations_index"),
    # Discord Administration Routes
    path("admin/discord", DiscordAdminIndex.as_view(), name="discord_admin_index"),
    path(
        "admin/discord/delete-channels",
        delete_discord_channels,
        name="discord_admin_delete_channels",
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
