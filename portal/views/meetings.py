from typing import Any, Dict
from django.http import JsonResponse
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.views.decorators.cache import cache_page
from ..models import Meeting


def meeting_to_event(meeting: Meeting) -> Dict[str, Any]:
    return {
        "id": meeting.id,
        "title": meeting.display_name,
        "start": meeting.starts_at,
        "end": meeting.ends_at,
        "url": meeting.get_absolute_url(),
        "color": meeting.color,
    }


class MeetingIndexView(ListView):
    template_name = "portal/meetings/index.html"
    context_object_name = "meetings"

    # Fetch 5 most recent published meetings, calendar will fetch all from API separately
    def get_queryset(self):
        today = timezone.datetime.today()
        this_morning = timezone.datetime.combine(
            today, timezone.datetime.min.time(), tzinfo=today.tzinfo
        )

        queryset = Meeting.objects.filter(
            is_published=True, starts_at__gte=this_morning
        ).select_related()[:5]
        return queryset


class MeetingDetailView(DetailView):
    template_name = "portal/meetings/detail.html"
    model = Meeting
    context_object_name = "meeting"


@cache_page(60 * 15)
def meetings_api(request):
    start, end = request.GET.get("start"), request.GET.get("end")

    meetings = Meeting.objects.filter(is_published=True, starts_at__range=[start, end])

    events = list(map(meeting_to_event, meetings))
    return JsonResponse(events, safe=False)
