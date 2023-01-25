import logging
from time import sleep

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models.functions import Lower

from .models import *

logger = logging.getLogger(__name__)


admin.site.site_header = "RCOS IO Administration"
admin.site.site_title = "RCOS IO"

# Actions


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
class UserInline(admin.TabularInline):
    model = User
    extra = 1


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1


class MeetingAttendanceInline(admin.TabularInline):
    model = MeetingAttendance
    extra = 1


class MeetingAttendanceCodeInline(admin.TabularInline):
    model = MeetingAttendanceCode
    extra = 1


class StatusUpdateSubmissionInline(admin.StackedInline):
    model = StatusUpdateSubmission
    extra = 1


class ProjectPitchInline(admin.TabularInline):
    model = ProjectPitch
    extra = 1


class ProjectProposalInline(admin.TabularInline):
    model = ProjectProposal
    extra = 1


class ProjectPresentationInline(admin.TabularInline):
    model = ProjectPresentation
    extra = 1


class ProjectRepositoryInline(admin.TabularInline):
    model = ProjectRepository
    extra = 1


class MentorApplicationInline(admin.TabularInline):
    model = MentorApplication
    extra = 1


class SmallGroupInline(admin.TabularInline):
    model = SmallGroup
    extra = 1


# Model Admins


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ["id", "name"]}),
        ("Dates", {"fields": ["start_date", "end_date"]}),
        (
            "Deadlines",
            {
                "fields": [
                    "mentor_application_deadline",
                    "enrollment_deadline",
                    "project_enrollment_application_deadline",
                    "project_pitch_deadline",
                    "project_proposal_deadline",
                ]
            },
        ),
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
    pass


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
    list_filter = ("role", "organization", "is_approved", "enrollments__semester__name")
    exclude = ("username",)
    fieldsets = (
        (
            "Personal info",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "role",
                    "rcs_id",
                    "graduation_year",
                    "email",
                    "password",
                    "is_approved",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
        (
            "Linked Accounts",
            {"fields": ("organization", "github_username", "discord_user_id")},
        ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
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


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("display_name", "type", "starts_at", "is_published")
    search_fields = ("name", "type")
    list_filter = ("starts_at", "type", "is_published")
    inlines = (MeetingAttendanceCodeInline, MeetingAttendanceInline)
    actions = (make_published,)


@admin.register(SmallGroup)
class SmallGroupAdmin(admin.ModelAdmin):
    list_display = ("display_name", "location", "semester")
    search_fields = ("name", "location")
    list_filter = ("semester",)


@admin.register(StatusUpdate)
class StatusUpdateAdmin(admin.ModelAdmin):
    list_display = ("display_name", "semester", "opens_at", "closes_at")
    search_fields = ("name", "location")
    list_filter = ("semester", "opens_at")
    inlines = (StatusUpdateSubmissionInline,)


@admin.register(ProjectTag)
class ProjectTagAdmin(admin.ModelAdmin):
    pass
