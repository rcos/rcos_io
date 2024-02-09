import csv
import logging
from time import sleep

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponse

from portal.models import (
    Enrollment,
    Meeting,
    MeetingAttendance,
    MeetingAttendanceCode,
    MentorApplication,
    Organization,
    Project,
    ProjectPitch,
    ProjectPresentation,
    ProjectProposal,
    ProjectRepository,
    ProjectTag,
    Room,
    Semester,
    SmallGroup,
    StatusUpdateSubmission,
    User,
)

logger = logging.getLogger(__name__)


admin.site.site_header = "RCOS IO Administration"
admin.site.site_title = "RCOS IO"

# Actions

def export_enrollments_to_csv(modeladmin, request, queryset):
    filename = "RCOS Enrollments"

    # Set the appropriate response headers so the browser expects a CSV file download
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}.csv"'},
    )

    # Create a CSV writer that writes to the response
    writer = csv.writer(response)

    # Write the headers
    writer.writerow(
        ["semester", "rcsid", "email", "given name", "family name", "project"]
    )

    for enrollment in queryset.filter(user__role = User.RPI):
        writer.writerow(
            [
                enrollment.semester,
                enrollment.user.rcs_id,
                enrollment.user.rcs_id + "@rpi.edu",
                enrollment.user.first_name,
                enrollment.user.last_name,
                enrollment.project,
            ]
        )

    return response


export_enrollments_to_csv.short_description = "Export to CSV"  # short description


@admin.action(description="Mark selected as approved")
def make_approved(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description="Sync roles and channels on Discord")
def sync_discord(modeladmin, request, queryset):
    semester = Semester.get_active()

    for object in queryset:
        try:
            object.sync_discord(semester)
            logger.info(f"Synced Discord roles and channels for project {object}")
        except Exception as err:
            logger.exception(
                "Failed to sync Discord roles and channels for {object}", exc_info=err
            )
        print("Sleeping")
        sleep(1)
        print("Awake")


@admin.action(description="Mark selected as published")
def make_published(modeladmin, request, queryset):
    queryset.update(is_published=True)


# Inlines
class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


class UserInline(admin.TabularInline):
    model = User
    extra = 1


class EnrollmentInline(admin.TabularInline):
    classes = ["collapse"]
    model = Enrollment
    extra = 1


class MeetingAttendanceInline(admin.TabularInline):
    classes = ["collapse"]
    model = MeetingAttendance
    extra = 1


class MeetingAttendanceCodeInline(admin.TabularInline):
    classes = ["collapse"]
    model = MeetingAttendanceCode
    extra = 1


class StatusUpdateSubmissionInline(admin.StackedInline):
    classes = ["collapse"]
    model = StatusUpdateSubmission
    extra = 1


class ProjectPitchInline(admin.TabularInline):
    classes = ["collapse"]
    model = ProjectPitch
    extra = 1


class ProjectProposalInline(admin.TabularInline):
    classes = ["collapse"]
    model = ProjectProposal
    extra = 1


class ProjectPresentationInline(admin.TabularInline):
    classes = ["collapse"]
    model = ProjectPresentation
    extra = 1


class ProjectRepositoryInline(admin.TabularInline):
    classes = ["collapse"]
    model = ProjectRepository
    extra = 1


class MentorApplicationInline(admin.TabularInline):
    classes = ["collapse"]
    model = MentorApplication
    extra = 1


class SmallGroupInline(admin.TabularInline):
    classes = ["collapse"]
    model = SmallGroup
    extra = 1


# Model Admins


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("building", "room", "capacity")


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ["id", "name"]}),
        ("Dates", {"fields": ["start_date", "end_date"]}),
        (
            "Deadlines",
            {
                "classes": ("collapse",),
                "fields": [
                    "mentor_application_deadline",
                    "enrollment_deadline",
                    "project_enrollment_application_deadline",
                    "project_pitch_deadline",
                    "project_proposal_deadline",
                ],
            },
        ),
        ("Rooms", {"fields": ("rooms",)}),
    )
    list_display = (
        "name",
        "start_date",
        "end_date",
        "enrollment_count",
        "project_count",
    )
    search_fields = ("name",)
    inlines = (
        MentorApplicationInline,
        ProjectPitchInline,
        ProjectProposalInline,
        ProjectPresentationInline,
        SmallGroupInline,
    )


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("name", "homepage_url", "logo_url")}),
        ("Emails", {"fields": (("email_domain", "email_domain_secondary"),)}),
        ("Discord", {"classes": ("collapse",), "fields": ("discord_role_id",)}),
    )


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("display_name", "role", "is_approved")
    search_fields = (
        "first_name",
        "last_name",
        "email",
        "rcs_id",
        "discord_user_id",
        "github_username",
    )
    list_filter = ("role", "organization", "is_approved", "enrollments__semester__name", "enrollments__credits", "enrollments__project__name")
    exclude = ("username",)
    fieldsets = (
        (
            "Personal info",
            {
                "fields": (
                    ("first_name", "last_name"),
                    "role",
                    "rcs_id",
                    "graduation_year",
                    "is_name_public"
                )
            },
        ),
        ("Account", {"fields": ("email", "password", "is_approved")}),
        (
            "Important dates",
            {"classes": ["collapse"], "fields": (("last_login", "date_joined"),)},
        ),
        (
            "Linked Accounts",
            {
                "classes": ["collapse"],
                "fields": ("organization", "github_username", "discord_user_id"),
            },
        ),
        (
            "Permissions",
            {
                "classes": ["collapse"],
                "fields": ("is_active", "is_staff", "is_superuser"),
            },
        ),
    )
    ordering = ("first_name",)
    inlines = (EnrollmentInline,)
    actions = (make_approved,)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "is_approved")
    search_fields = ("name", "description", "tags__name")
    list_filter = (
        "is_approved",
        "organization",
        "enrollments__semester__name",
        "tags__name",
    )
    inlines = (
        ProjectRepositoryInline,
        EnrollmentInline,
        ProjectPitchInline,
        ProjectProposalInline,
        ProjectPresentationInline,
    )
    prepopulated_fields = {"slug": ("name",)}
    actions = (
        make_approved,
        sync_discord,
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("name", "slug"),
                    "owner",
                    "organization",
                    "is_approved",
                    "description",
                    "tags",
                )
            },
        ),
        (
            "Links",
            {
                "classes": ["collapse"],
                "fields": ("homepage_url", "logo_url", "external_chat_url"),
            },
        ),
        (
            "Discord",
            {
                "classes": ["collapse"],
                "fields": (
                    "discord_role_id",
                    "discord_text_channel_id",
                    "discord_voice_channel_id",
                ),
            },
        ),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "owner":
            parent_id = request.resolver_match.kwargs.get("object_id")

            try:
                project = Project.objects.get(pk=parent_id)

                if project.organization:
                    kwargs["queryset"] = project.organization.users.filter(
                        is_approved=True
                    )
                else:
                    kwargs["queryset"] = User.objects.filter(is_approved=True)
            except Project.DoesNotExist:
                pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "semester", "project")
    list_filter = (
        "semester__name",
        "credits",
        "is_for_pay",
        "is_project_lead",
        "is_coordinator",
        "is_mentor",
    )
    search_fields = (
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__rcs_id",
        "user__discord_user_id",
        "user__github_username",
    )

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "semester",
                    "user",
                    "project",
                )
            },
        ),
        (
            "Roles",
            {
                "fields": (
                    (
                        "is_project_lead",
                        "is_mentor",
                        "is_coordinator",
                        "is_faculty_advisor",
                    ),
                )
            },
        ),
        (
            "Grading",
            {"fields": ("credits", "is_for_pay", "final_grade", "notes_markdown")},
        ),
    )

    actions = [export_enrollments_to_csv]


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("display_name", "type", "starts_at", "is_published")
    search_fields = ("name", "type")
    list_filter = ("starts_at", "type", "is_published")
    inlines = (MeetingAttendanceCodeInline, MeetingAttendanceInline)
    actions = (make_published,)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "semester",
                    "name",
                    "type",
                    "is_published",
                    "is_attendance_taken",
                    "room",
                    ("starts_at", "ends_at"),
                    "host",
                    "description_markdown",
                )
            },
        ),
        ("Links", {"fields": ("presentation_url", "recording_url")}),
        (
            "Advanced info",
            {
                "classes": ("collapse",),
                "fields": (
                    "attendance_chance_verification_required",
                    "discord_event_id",
                ),
            },
        ),
    )


@admin.register(SmallGroup)
class SmallGroupAdmin(admin.ModelAdmin):
    list_display = ("display_name", "room", "semester")
    search_fields = ("name", "room")
    list_filter = ("semester",)

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "semester",
                    "name",
                    "room",
                )
            },
        ),
        (
            "Assignments",
            {"fields": ("projects", "mentors")},
        ),
        (
            "Discord",
            {
                "classes": ("collapse",),
                "fields": ("discord_category_id", "discord_role_id"),
            },
        ),
    )


# @admin.register(StatusUpdate)
# class StatusUpdateAdmin(admin.ModelAdmin):
#     list_display = ("display_name", "semester", "opens_at", "closes_at")
#     search_fields = ("name", "room")
#     list_filter = ("semester", "opens_at")
#     inlines = (StatusUpdateSubmissionInline,)


@admin.register(ProjectTag)
class ProjectTagAdmin(admin.ModelAdmin):
    pass
