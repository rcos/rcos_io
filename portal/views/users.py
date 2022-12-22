from . import SemesterFilteredListView, SemesterFilteredDetailView
from ..models import User


class UserIndexView(SemesterFilteredListView):
    template_name = "portal/users/index.html"
    context_object_name = "users"

    # Default to all active RPI members
    queryset = User.objects.filter(is_active=True, is_approved=True, role="rpi")
    semester_filter_key = "enrollments__semester"


class UserDetailView(SemesterFilteredDetailView):
    template_name = "portal/users/detail.html"
    model = User
    context_object_name = "user"
