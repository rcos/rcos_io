from django.views.generic.base import TemplateView

from portal.models import Enrollment, Project


class IndexView(TemplateView):
    template_name = "portal/index/index.html"

    def get_context_data(self, **kwargs):
        data =  super().get_context_data(**kwargs)
        data["enrollment_count"] = Enrollment.objects.count()
        data["project_count"] = Project.objects.count()
        return data