from . import SemesterFilteredListView, SearchableListView
from ..models import SmallGroup


class SmallGroupIndexView(SearchableListView, SemesterFilteredListView):
    template_name = "portal/small_groups/index.html"
    context_object_name = "small_groups"

    model = SmallGroup
    search_fields = (
        "name",
        "projects__name",
        "mentors__rcs_id"
    )