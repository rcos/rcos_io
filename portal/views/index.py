
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from django.views.generic.base import TemplateView

from portal.forms import SubmitAttendanceForm
from portal.models import Enrollment, Meeting, Project


class IndexView(TemplateView):
    template_name = "portal/index/index.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        active_semester = cache.get("active_semester")
        data["next_meeting"] = (
            Meeting.get_user_queryset(self.request.user)
            .filter(ends_at__gte=timezone.now())
            .first()
        )

        if self.request.user.is_authenticated:
            data["ongoing_meeting"] = Meeting.get_ongoing(self.request.user)
        else:
            data["ongoing_meeting"] = None
            data["submit_attendance_form"] = SubmitAttendanceForm()
            data["enrollment_count"] = cache.get_or_set(
                "enrollment_count", Enrollment.objects.count(), 60 * 60 * 24
            )
            data["project_count"] = cache.get_or_set(
                "project_count", Project.objects.count(), 60 * 60 * 24
            )
            data["active_semester_admins"] = cache.get_or_set(
                "active_semester_admins",
                Enrollment.objects.filter(
                    Q(is_faculty_advisor=True) | Q(is_coordinator=True),
                    semester=active_semester,
                ),
                60 * 60 * 24,
            )

        return data


class HandbookView(TemplateView):
    template_name = "portal/index/handbook.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["initial_route"] = self.request.GET.get("initial_route")
        return data
