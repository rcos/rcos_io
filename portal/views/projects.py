from django.contrib.postgres.search import SearchVector
from . import SemesterFilteredListView, SemesterFilteredDetailView, SearchableListView
from ..models import Enrollment, Project
from portal.services import github


class ProjectIndexView(SearchableListView, SemesterFilteredListView):
    template_name = "portal/projects/index.html"
    context_object_name = "projects"

    # Default to all approved projects
    queryset = Project.objects.filter(is_approved=True)
    semester_filter_key = "enrollments__semester"
    search_fields = (
        "name",
        "owner__first_name",
        "owner__last_name",
        "owner__rcs_id",
        "summary",
        "tags__name",
    )

    def get_queryset(self):
        """Apply filters (semester is already handled)"""
        queryset = super().get_queryset()

        self.is_seeking_members = self.request.GET.get("is_seeking_members") == "yes"
        if self.is_seeking_members:
            queryset = queryset.filter(is_seeking_members=True)
            self.is_seeking_members = True

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["is_seeking_members"] = self.is_seeking_members
        return data


class ProjectDetailView(SemesterFilteredDetailView):
    template_name = "portal/projects/detail.html"
    model = Project
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        if "target_semester" in data:
            data["target_semester_enrollments"] = Enrollment.objects.filter(
                semester=data["target_semester"], project=self.object
            )
        else:
            enrollments_by_semester = {}
            for enrollment in self.object.enrollments.all():
                if enrollment.semester not in enrollments_by_semester:
                    enrollments_by_semester[enrollment.semester] = []
                enrollments_by_semester[enrollment.semester].append(enrollment)
            data["enrollments_by_semester"] = enrollments_by_semester
        client = github.client_factory()
        data["repositories"] = [
            github.get_repository_details(client, repo.url)["repository"]
            for repo in self.object.repositories.all()
        ]

        return data
