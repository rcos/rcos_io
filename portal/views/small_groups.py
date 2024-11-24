"""Views related to small groups."""
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from ..models import SmallGroup
from . import SearchableListView, SemesterFilteredListView

@method_decorator(login_required, name="dispatch")
class SmallGroupIndexView(SearchableListView, SemesterFilteredListView):
    require_semester = True
    template_name = "portal/small_groups/index.html"
    context_object_name = "small_groups"
    queryset = SmallGroup.objects.select_related()
    search_fields = (
        "name",
        "projects__name",
        "mentors__rcs_id",
        "mentors__first_name",
        "mentors__last_name",
    )

@login_required
def small_group_detail(request: HttpRequest, pk: int) -> HttpResponse:
    """Fetches and displays an overview for a particular small group."""
    return TemplateResponse(request, "portal/small_groups/detail.html", {
        "small_group": get_object_or_404(SmallGroup, pk=pk)
    })
