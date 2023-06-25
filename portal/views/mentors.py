"""Views relating to mentors and the actions they can take."""
from typing import Any

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView

from portal.checks import CheckUserCanApplyAsMentor
from portal.forms import MentorApplicationForm

from ..models import ProjectTag, Semester
from . import (
    target_semester_context,
)


def mentor_applications_index(request: HttpRequest) -> HttpResponse:
    context: dict[str, Any] = target_semester_context(request)

    if "target_semester" in context:
        context["pending_applications"] = context["target_semester"].mentor_applications.filter(is_accepted__isnull=True)
        context["accepted_applications"] = context["target_semester"].mentor_applications.filter(is_accepted=True)
        context["denied_applications"] = context["target_semester"].mentor_applications.filter(is_accepted=False)

        context["tags_with_counts"] = ProjectTag.objects.annotate(
            pending_application_count=Count("mentor_applications", filter=Q(mentor_applications__is_accepted__isnull=True, mentor_applications__semester=context["target_semester"])),
            accepted_application_count=Count("mentor_applications", filter=Q(mentor_applications__is_accepted=True, mentor_applications__semester=context["target_semester"]))
        ).order_by("-pending_application_count")
    else:
        context["semesters"] = Semester.objects.all()
    return TemplateResponse(request, "portal/mentors/index.html", context)

class MentorApplicationView(
    SuccessMessageMixin, LoginRequiredMixin, CreateView
):
    form_class = MentorApplicationForm
    template_name = "portal/mentors/application.html"
    success_message = "Your application has been submitted and will be reviwed " \
        "by the Coordinators and Faculty Advisors shortly."
    success_url = reverse_lazy("users_index")

    def get(self, request, *args, **kwargs):
        active_semester = Semester.get_active()

        check = CheckUserCanApplyAsMentor().check(self.request.user, active_semester)
        if not check.passed:
            messages.error(
                self.request,
                "You are not currently eligible to propose new projects: " \
                    f"{check.fail_reason}",
            )
            return redirect(reverse("users_index"))

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        active_semester = Semester.get_active()
        check = CheckUserCanApplyAsMentor().check(self.request.user, active_semester)
        if not check.passed:
            messages.error(
                self.request,
                f"You are not currently eligible to propose new projects: {check.fail_reason}",
            )
            return redirect(reverse("users_index"))

        form.instance.semester = active_semester
        form.instance.user = self.request.user

        # TODO: message admins on Discord

        return super().form_valid(form)
