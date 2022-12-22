from django.contrib.postgres.search import SearchVector
from . import SemesterFilteredListView, SemesterFilteredDetailView
from ..models import Project


class ProjectIndexView(SemesterFilteredListView):
    template_name = "portal/projects/index.html"
    context_object_name = "projects"

    # Default to all approved projects
    queryset = Project.objects.filter(is_approved=True)
    semester_filter_key = "enrollments__semester"

    def get_queryset(self):
        """Apply filters (semester is already handled)"""
        queryset = super().get_queryset()

        self.is_seeking_members = self.request.GET.get("is_seeking_members") == "yes"
        if self.is_seeking_members:
            queryset = queryset.filter(is_seeking_members=True)
            self.is_seeking_members = True

        self.search = self.request.GET.get("search")
        if self.search:
            queryset = queryset.annotate(
                search=SearchVector(
                    "name",
                    "owner__first_name",
                    "owner__last_name",
                    "summary",
                    "description_markdown",
                    "tags__name",
                ),
            ).filter(search=self.search)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["is_seeking_members"] = self.is_seeking_members
        data["search"] = self.search
        return data


class ProjectDetailView(SemesterFilteredDetailView):
    template_name = "portal/projects/detail.html"
    model = Project
    context_object_name = "project"
