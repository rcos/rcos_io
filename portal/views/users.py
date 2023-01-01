from django.views.generic.edit import CreateView, DeleteView, UpdateView
from . import SemesterFilteredListView, SemesterFilteredDetailView, SearchableListView
from ..models import User, Enrollment


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


class EnrollmentCreateView(CreateView):
    model = Enrollment
    fields = ["semester"]
    template_name = "portal/users/enroll.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.user = self.request.user
        return super().form_valid(form)