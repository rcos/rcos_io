from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, InvalidPage, PageNotAnInteger, Paginator
from django.shortcuts import redirect
from django.urls import reverse

from ..models import Enrollment, Project, Semester, User
from . import SearchableListView, SemesterFilteredDetailView, SemesterFilteredListView


class UserIndexView(SearchableListView, SemesterFilteredListView):
    template_name = "portal/users/index.html"
    context_object_name = "users"
    paginate_by = 50

    # Default to all active RPI members
    queryset = User.rpi

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

        paginator = Paginator(self.get_queryset(), self.paginate_by)

        page = self.request.GET.get("page")

        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except (EmptyPage, InvalidPage):
            users = paginator.page(paginator.num_pages)

        enrollments = Enrollment.objects.filter(user__in=users).select_related(
            "semester", "project"
        )

        if self.target_semester:
            enrollments = enrollments.filter(semester=self.target_semester)

        user_rows = []
        for user in users:
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
                user_row["enrollments"] = [
                    e for e in enrollments if e.user_id == user.pk
                ]

            user_rows.append(user_row)

        data["user_rows"] = user_rows

        return data


class UserDetailView(SemesterFilteredDetailView):
    template_name = "portal/users/detail.html"
    model = User
    context_object_name = "user"


@login_required
def enroll_user(request, pk: str):
    if not request.user.is_setup:
        messages.error(
            request,
            "Please fill your profile out and connect your Discord and GitHub first.",
        )
        return redirect(reverse("profile"))

    if request.method == "POST":
        semester = Semester.objects.get(pk=request.POST["semester"])

        user = User.objects.get(pk=pk)

        project = None
        if request.POST.get("project", None):
            project = Project.objects.get(pk=request.POST.get("project", None))

        credits = 0
        if request.POST.get("credits", 0):
            credits = int(request.POST.get("credits", 0))

        is_project_lead = request.POST.get("is_project_lead", None) == "on"

        messages.success(request, "Confirmed your enrollment!")
        enrollment, is_new = Enrollment.objects.update_or_create(
            user=user,
            semester=semester,
            defaults={"project": project, "credits": credits, "is_project_lead": is_project_lead},
        )

    return redirect("/")
