from urllib import request
from django.views.generic.base import TemplateView

from portal.forms import SubmitAttendanceForm
from portal.models import Enrollment, Meeting, Project, Semester
from django.utils import timezone

from django.core.cache import cache


class IndexView(TemplateView):
    template_name = "portal/index/index.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        active_semester = cache.get("active_semester")
        data["submit_attendance_form"] = SubmitAttendanceForm()
        data["enrollment_count"] = Enrollment.objects.count()
        data["project_count"] = Project.objects.count()
        data["active_semester_coordinators"] = Enrollment.objects.filter(
            semester=active_semester, is_coordinator=True
        )
        data["next_meeting"] = (
            Meeting.get_user_queryset(self.request.user)
            .filter(ends_at__gte=timezone.now())
            .first()
        )

        if self.request.user.is_authenticated:
            active_semester = Semester.get_active()
            data["ongoing_meeting"] = Meeting.get_ongoing(self.request.user)
            data["can_propose_project"] = self.request.user.can_propose_project(
                active_semester
            )
            data["pending_project"] = self.request.user.owned_projects.filter(
                is_approved=False
            ).first()
        else:
            data["ongoing_meeting"] = None
            data["can_propose_project"] = None
            data["pending_project"] = None

        return data


class HandbookView(TemplateView):
    template_name = "portal/index/handbook.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["initial_route"] = self.request.GET.get("initial_route")
        return data
