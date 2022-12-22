from django.contrib.postgres.search import SearchVector
from . import SemesterFilteredListView, SemesterFilteredDetailView
from ..models import User


class UserIndexView(SemesterFilteredListView):
    template_name = "portal/users/index.html"
    context_object_name = "users"

    # Default to all active RPI members
    queryset = User.objects.filter(is_active=True, is_approved=True, role="rpi")
    semester_filter_key = "enrollments__semester"

    def get_queryset(self):
        """Apply filters (semester is already handled)"""
        queryset = super().get_queryset()

        self.search = self.request.GET.get("search")
        if self.search:
            queryset = queryset.annotate(
                search=SearchVector(
                    "first_name",
                    "last_name",
                    "rcs_id",
                    "graduation_year"
                ),
            ).filter(search=self.search)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["search"] = self.search
        return data


class UserDetailView(SemesterFilteredDetailView):
    template_name = "portal/users/detail.html"
    model = User
    context_object_name = "user"
