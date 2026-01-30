from typing import Any

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, InvalidPage, PageNotAnInteger, Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from ..models import Enrollment, Organization, Project, Semester, User
from . import (
    OrganizationFilteredListView,
    SearchableListView,
    SemesterFilteredListView,
    target_semester_context,
)


class UserIndexView(SearchableListView, OrganizationFilteredListView, SemesterFilteredListView):
    template_name = "portal/users/index.html"
    context_object_name = "users"
    paginate_by = 50

    # Default to all active RPI members
    queryset = User.objects.approved().select_related("organization")

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

        data["organizations"] = Organization.objects.all()
        
        # Cache the queryset to avoid multiple evaluations
        queryset = self.get_queryset()
        data["total_count"] = queryset.count()

        paginator = Paginator(queryset, self.paginate_by)  # Reuse same queryset

        page = self.request.GET.get("page")

        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except (EmptyPage, InvalidPage):
            users = paginator.page(paginator.num_pages)

        # Get user IDs for the current page to filter enrollments
        user_ids = [u.pk for u in users]
        
        # Build enrollment query with all needed relations
        enrollments_query = Enrollment.objects.filter(user_id__in=user_ids).select_related(
            "semester", "project"
        )

        if self.target_semester:
            enrollments_query = enrollments_query.filter(semester=self.target_semester)
        
        enrollments_list = list(enrollments_query)
        enrollments_by_user = {}
        for e in enrollments_list:
            enrollments_by_user.setdefault(e.user_id, []).append(e)

        user_rows = []
        for user in users:
            user_row = {
                "user": user,
            }
            user_enrollments = enrollments_by_user.get(user.pk, [])

            if self.target_semester:
                user_row["enrollment"] = user_enrollments[0] if user_enrollments else None
                user_row["project"] = (
                    user_row["enrollment"].project if user_row["enrollment"] else None
                )
            else:
                user_row["enrollments"] = user_enrollments

            user_rows.append(user_row)

        data["user_rows"] = user_rows

        return data


def user_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Fetches the profile of a an approved, active user."""
    user: User = get_object_or_404(User.objects.approved(), pk=pk)
    context: dict[str, Any] = {
        "user": user,
    } | target_semester_context(request)

    if "target_semester" in context:
        # Add select_related to avoid N+1 when accessing project in template
        context["enrollment"] = Enrollment.objects.filter(
            semester_id=context["target_semester"].pk, 
            user_id=user.pk
        ).select_related("semester", "project").first()
    else:
        context["enrollments"] = user.enrollments.select_related("semester", "project")

    return TemplateResponse(request, "portal/users/detail.html", context)

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
