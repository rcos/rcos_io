from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import *

admin.site.site_header = "RCOS IO Administration"
admin.site.site_title = "RCOS IO"

# Actions


@admin.action(description="Mark selected as approved")
def make_approved(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description="Mark selected as published")
def make_published(modeladmin, request, queryset):
    queryset.update(is_published=True)


# Inlines
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


# Model Admins


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ["id", "name"]}),
        ("Dates", {"fields": ["start_date", "end_date"]}),
        (None, {"fields": ["is_accepting_new_projects"]}),
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
        EnrollmentInline,
        ProjectPitchInline,
        ProjectProposalInline,
        ProjectPresentationInline,
    )


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ("display_name", "role", "is_approved")
    search_fields = ("first_name", "last_name", "email", "rcs_id", "discord_user_id", "github_username")
    list_filter = ("role", "is_approved", "enrollments__semester__name")
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
        ("Linked Accounts", {"fields": ("github_username", "discord_user_id")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
    )
    ordering = ("email", "last_login")
    inlines = (EnrollmentInline,)
    actions = (make_approved,)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "summary", "created_at", "is_approved")
    search_fields = ("name", "summary", "tags__name")
    list_filter = ("is_approved", "enrollments__semester__name", "tags__name")
    inlines = (
        ProjectRepositoryInline,
        EnrollmentInline,
        ProjectPitchInline,
        ProjectProposalInline,
        ProjectPresentationInline,
    )
    prepopulated_fields = {"slug": ("name",)}
    actions = (make_approved,)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "semester", "project")
    list_filter = (
        "semester__name",
        "credits",
        "is_for_pay",
        "is_project_lead",
        "is_coordinator",
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
