from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.urls import reverse

from ..models import Enrollment, Semester, User
from . import SearchableListView, SemesterFilteredDetailView, SemesterFilteredListView


class UserIndexView(SearchableListView, SemesterFilteredListView):
    template_name = "portal/users/index.html"
    context_object_name = "users"

    # Default to all active RPI members
    queryset = User.objects.filter(
        is_active=True, is_approved=True, role="rpi"
    ).select_related()
    semester_filter_key = "enrollments__semester"
    search_fields = (
        "first_name",
        "last_name",
        "rcs_id",
        "graduation_year",
        "enrollments__project__name",
    )


class UserDetailView(SemesterFilteredDetailView):
    template_name = "portal/users/detail.html"
    model = User
    context_object_name = "user"


@login_required
def enroll_user(request):
    if not request.user.is_setup:
        messages.error(
            request,
            "Please fill your profile out and connect your Discord and GitHub before enrolling.",
        )
        return redirect(reverse("profile"))

    if request.method == "POST":
        semester = Semester.objects.get(pk=request.POST["semester"])
        messages.success(request, f"Welcome to RCOS {semester}!")
        Enrollment(user=request.user, semester=semester).save()
    return redirect("/")
