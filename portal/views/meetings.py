import random
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView

from portal.forms import SubmitAttendanceCodeForm

from ..models import Meeting, MeetingAttendance, MeetingAttendanceCode


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


class SubmitAttendanceFormView(FormView):
    template_name = "portal/meetings/attendance/submit.html"
    form_class = SubmitAttendanceCodeForm
    success_url = "/"

    def form_valid(self, form: SubmitAttendanceCodeForm):
        code = form.cleaned_data["code"]
        user = self.request.user

        try:
            meeting_attendance_code = MeetingAttendanceCode.objects.get(pk=code)
        except MeetingAttendanceCode.DoesNotExist:
            messages.error(
                self.request,
                "Attendance code not recognized. Your attendance was not recorded.",
            )
            return super().form_valid(form)

        if meeting_attendance_code.is_valid:
            # Confirm user is in small group if it is for a small group
            if (
                meeting_attendance_code.small_group
                and not meeting_attendance_code.small_group.has_user(user)
            ):
                messages.warning(
                    self.request,
                    "That is not your Small Group's attendance code... Nice try.",
                )
                return redirect("/")

            new_attendance = MeetingAttendance(
                meeting=meeting_attendance_code.meeting,
                user=user,
                is_verified=random.random() > 0.5,
            )
            new_attendance.save()

            if new_attendance.is_verified:
                messages.success(
                    self.request,
                    f"Your attendance at {meeting_attendance_code.meeting} has been recorded!",
                )
            else:
                messages.warning(
                    self.request,
                    f"VERIFICATION REQUIRED! Contact your Small Group Mentor to verify your attendance at {meeting_attendance_code.meeting}.",
                )
        else:
            messages.error(
                self.request,
                "That attendance code is no longer valid. Your attendance was not recorded.",
            )

        return super().form_valid(form)
