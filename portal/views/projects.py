from django.views.generic import DetailView

from . import SemesterFilteredListView
from ..models import Project


class ProjectIndexView(SemesterFilteredListView):
    template_name = "portal/projects/index.html"
    context_object_name = "projects"

    # Default to all approved projects
    queryset = Project.objects.filter(is_approved=True)
    semester_filter_key = "enrollments__semester"


class ProjectDetailView(DetailView):
    template_name = "portal/projects/detail.html"
    model = Project
    context_object_name = "project"
