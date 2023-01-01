from django.views.generic.base import TemplateView

from portal.models import Enrollment, Meeting, Project


class IndexView(TemplateView):
    template_name = "portal/index/index.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["enrollment_count"] = Enrollment.objects.count()
        data["project_count"] = Project.objects.count()
        data["active_semester_coordinators"] = Enrollment.objects.filter(
            is_coordinator=True
        )
        data["next_meeting"] = Meeting.get_next()
        return data


class HandbookView(TemplateView):
    template_name = "portal/index/handbook.html"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["initial_route"] = self.request.GET.get("initial_route")
        return data
