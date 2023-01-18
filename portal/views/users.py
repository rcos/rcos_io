from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect
from django.urls import reverse

from ..models import Enrollment, Semester, User
from . import SearchableListView, SemesterFilteredDetailView, SemesterFilteredListView


class UserIndexView(SearchableListView, SemesterFilteredListView):
    paginate_by = 50
    template_name = "portal/users/index.html"
    context_object_name = "users"

    # Default to all active RPI members
    queryset = User.objects.filter(role=User.RPI, is_approved=True, is_active=True)

    semester_filter_key = "enrollments__semester"
    search_fields = (
        "first_name",
        "last_name",
        "rcs_id",
        "graduation_year",
        "enrollments__project__name",
    )

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        enrollments = Enrollment.objects.filter(
            user__in=self.get_queryset()
        ).select_related("semester", "project")

        if self.target_semester:
            enrollments = enrollments.filter(semester=self.target_semester)

        user_rows = []
        for user in self.get_queryset():
            user_row = {
                "user": user,
            }

            if self.target_semester:
                user_row["enrollment"] = next(
                    (e for e in enrollments if e.user_id == user.pk), None
                )
                user_row["project"] = (
                    user_row["enrollment"].project if user_row["enrollment"] else None
                )
            else:
                user_row["enrollments"] = []

            user_rows.append(user_row)

        data["user_rows"] = user_rows

        return data


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
