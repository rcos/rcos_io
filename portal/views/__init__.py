from django.contrib.postgres.search import SearchVector
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from ..models import Semester


def load_semesters(request):
    semesters = Semester.objects.all()
    active_semester = next(
        (semester for semester in semesters if semester.is_active), None
    )

    return {"semesters": semesters, "active_semester": active_semester}


class SemesterFilteredDetailView(DetailView):
    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        semester_id = self.request.GET.get("semester")
        if semester_id:
            data["target_semester"] = get_object_or_404(Semester, pk=semester_id)

        return data


class SemesterFilteredListView(ListView):
    """
    Render some list of objects, set by self.model or self.queryset. self.queryset can actually be any iterable of items, not just a queryset.

    If `semester` query parameter is present AND valid:
        - finds semester and passes it to template as `target_semester`
        - filters queryset with `<self.semester_filter_key>=target_semester`

    If `semester`is present and INVALID:
        - throws a 404

    Example:
    ```
    class ProjectIndexView(SemesterFilteredListView):
        template_name = "portal/projects/index.html"
        context_object_name = "projects"

        # Default to all approved projects
        queryset = Project.objects.filter(is_approved=True)
        # Filter projects where `enrollments__semester` == the semester with the ID passed in the URL (if present)
        semester_filter_key = "enrollments__semester"
    ```
    """

    semester_filter_key = "semester"
    """The key to match with the semester object when filtering."""

    def get_queryset(self):
        """Default to queryset, and filters down to a particular semester if requested."""
        queryset = super().get_queryset()

        semester_id = self.request.GET.get("semester")
        if semester_id:
            self.target_semester = get_object_or_404(Semester, pk=semester_id)

            return queryset.filter(**{self.semester_filter_key: self.target_semester})
        else:
            self.target_semester = None

        return queryset

    def get_context_data(self, **kwargs):
        """Expose `target_semester` to the template if present."""
        data = super().get_context_data(**kwargs)
        data["target_semester"] = self.target_semester
        return data


class SearchableListView(ListView):
    """
    Render some list of objects, set by self.model or self.queryset. self.queryset can actually be any iterable of items, not just a queryset.

    If `search` query parameter is present AND valid:
        - filters queryset by searching through columns `self.search_fields`

    Example:
    ```
    class ProjectIndexView(SearchableListView):
        template_name = "portal/projects/index.html"
        context_object_name = "projects"

        # Default to all approved projects
        queryset = Project.objects.filter(is_approved=True)
        # If search is passed in URL, search that value on these fields
        search_fields = ("name", "summary", "owner__rcs_id)
    ```
    """

    search_fields = tuple()

    def get_queryset(self):
        """Apply search"""
        queryset = super().get_queryset()

        self.search = self.request.GET.get("search")
        if self.search:
            queryset = queryset.annotate(
                search=SearchVector(*self.search_fields),
            ).filter(search=self.search)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data["search"] = self.search
        return data
