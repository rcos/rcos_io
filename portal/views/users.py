from django.views.generic import DetailView

from . import SemesterFilteredListView
from ..models import User


class UserIndexView(SemesterFilteredListView):
    template_name = "portal/users/index.html"
    context_object_name = "users"

    # Default to all approved users
    queryset = User.objects.filter(is_approved=True)
    semester_filter_key = "enrollments__semester"


class UserDetailView(DetailView):
    template_name = "portal/users/detail.html"
    model = User
    context_object_name = "user"
