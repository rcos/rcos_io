from django.http import HttpResponse
from django.core.serializers import serialize
from django.views.generic import ListView, DetailView
from ..models import Meeting


class MeetingIndexView(ListView):
    template_name = "portal/meetings/index.html"
    context_object_name = "meetings"

    # Only show published meetings
    queryset = Meeting.objects.filter(is_published=True)


class MeetingDetailView(DetailView):
    template_name = "portal/meetings/detail.html"
    model = Meeting
    context_object_name = "meeting"


def meetings_api(request):
    meetings = Meeting.objects.filter(is_published=True)
    data = serialize(
        "json", meetings, fields=("name", "type", "starts_at", "ends_at", "location")
    )
    return HttpResponse(data, content_type="application/json")
