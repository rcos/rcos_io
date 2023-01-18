from django.views.generic import DetailView

from ..models import SmallGroup
from . import SearchableListView, SemesterFilteredListView


class SmallGroupIndexView(SearchableListView, SemesterFilteredListView):
    template_name = "portal/small_groups/index.html"
    context_object_name = "small_groups"
    queryset = SmallGroup.objects.select_related()
    search_fields = ("name", "projects__name", "mentors__rcs_id")


class SmallGroupDetailView(DetailView):
    template_name = "portal/small_groups/detail.html"
    model = SmallGroup
    context_object_name = "small_group"
