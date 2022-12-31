from django.contrib.postgres.search import SearchVector
from . import SemesterFilteredListView, SemesterFilteredDetailView, SearchableListView
from ..models import User


class UserIndexView(SearchableListView, SemesterFilteredListView):
    template_name = "portal/users/index.html"
    context_object_name = "users"

    # Default to all active RPI members
    queryset = User.objects.filter(
        is_active=True, is_approved=True, role="rpi"
    ).select_related()
    semester_filter_key = "enrollments__semester"
    search_fields = (
        "first_name",
        "last_name",
        "rcs_id",
        "graduation_year",
        "enrollments__project__name",
    )


class UserDetailView(SemesterFilteredDetailView):
    template_name = "portal/users/detail.html"
    model = User
    context_object_name = "user"
