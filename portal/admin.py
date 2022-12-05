from django.contrib import admin

from .models import *

admin.site.site_header = "RCOS IO Administration"

# Inlines
class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1

class MeetingAttendanceInline(admin.TabularInline):
    model = MeetingAttendance
    extra = 1

# Model Admins

class SemesterAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["id", "name"]}),
        ("Dates", {"fields": ["start_date", "end_date"]}),
        (None, {"fields": ["is_accepting_new_projects"]})
    ]
    list_display = ("name", "start_date", "end_date", "enrollment_count", "project_count")
    search_fields = ["name"]
    inlines = [EnrollmentInline]

class UserAdmin(admin.ModelAdmin):
    list_display = ("is_approved", "full_name", "role", "email")
    search_fields = ("first_name", "last_name", "email", "rcs_id")
    list_filter = ("role", "is_approved", "enrollments__semester__name")

class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "tagline")
    search_fields = ("name", "tagline")
    list_filter = ("is_approved", "enrollments__semester__name")
    inlines = [EnrollmentInline]

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("semester", "user", "project")
    list_filter = ("semester__name", "credits", "is_for_pay", "is_project_lead", "is_coordinator")

class MeetingAdmin(admin.ModelAdmin):
    list_display = ("is_published", "name", "type", "starts_at")
    search_fields = ("name", "type")
    list_filter = ("starts_at", "type", "is_published")
    inlines = [MeetingAttendanceInline]

admin.site.register(Semester, SemesterAdmin)
admin.site.register(User, UserAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)
admin.site.register(Meeting, MeetingAdmin)