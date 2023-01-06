import random
import string
from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView

from portal.forms import SubmitAttendanceForm

from ..models import (
    Enrollment,
    Meeting,
    MeetingAttendance,
    MeetingAttendanceCode,
    SmallGroup,
    User,
)


def generate_code(code_length: int = 5):
    """
    Generates & returns a new attendance code.
    """

    code = ""

    for _ in range(code_length):
        code += random.choice(string.ascii_uppercase)

    return code


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
    object: Meeting
    template_name = "portal/meetings/detail.html"
    model = Meeting
    context_object_name = "meeting"

    def can_manage_attendance(self):
        if not self.request.user.is_authenticated:
            return False
        if self.request.user.is_superuser:
            return True

        if self.request.user.is_mentor(self.object.semester):
            return True

        return False

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        data["can_manage_attendance"] = False
        if self.can_manage_attendance():
            data["can_manage_attendance"] = True
            expected_users = User.objects.filter(
                enrollments__semester=self.object.semester
            )
            attended_users = self.object.attendances.filter(
                meetingattendance__is_verified=True
            )
            non_attended_users = expected_users.exclude(
                pk__in=attended_users.values_list("pk", flat=True)
            )
            needs_verification_users = self.object.attendances.filter(
                meetingattendance__is_verified=False
            )

            small_group_pk = self.request.GET.get("small_group")
            small_group = None
            if small_group_pk:
                small_group = SmallGroup.objects.get(pk=small_group_pk)
                small_group_user_ids = small_group.get_users().values_list(
                    "pk", flat=True
                )
                attended_users = attended_users.filter(pk__in=small_group_user_ids)
                non_attended_users = non_attended_users.filter(
                    pk__in=small_group_user_ids
                )
                needs_verification_users = needs_verification_users.filter(
                    pk__in=small_group_user_ids
                )

            data["target_small_group"] = small_group
            data["attended_users"] = attended_users
            data["non_attended_users"] = non_attended_users
            data["needs_verification_users"] = needs_verification_users
            data["attendance_ratio"] = attended_users.count() / expected_users.count()

            query = {
                "meeting": self.object,
            }
            if small_group:
                query["small_group"] = small_group
            else:
                query["small_group__isnull"] = True

            if self.object.is_ongoing:
                code, is_code_new = self.object.attendance_codes.get_or_create(
                    **query,
                    defaults={"code": generate_code(), "small_group": small_group},
                )
            else:
                code = None

            data["code"] = code

        return data


@cache_page(60 * 15)
def meetings_api(request):
    start, end = request.GET.get("start"), request.GET.get("end")

    meetings = Meeting.objects.filter(is_published=True, starts_at__range=[start, end])

    events = list(map(meeting_to_event, meetings))
    return JsonResponse(events, safe=False)


class SubmitAttendanceFormView(FormView):
    template_name = "portal/meetings/attendance/submit.html"
    form_class = SubmitAttendanceForm
    success_url = "/"

    def form_valid(self, form: SubmitAttendanceForm):
        code = form.cleaned_data["code"]
        user = self.request.user

        if not user.is_authenticated:
            messages.error(
                self.request,
                "You are not logged in!",
            )
            return redirect("/")

        try:
            meeting_attendance_code = MeetingAttendanceCode.objects.get(pk=code)
        except MeetingAttendanceCode.DoesNotExist:
            messages.error(
                self.request,
                "Attendance code not recognized. Your attendance was not recorded.",
            )
            return super().form_valid(form)

        try:
            user.enrollments.get(semester=meeting_attendance_code.meeting.semester)
        except Enrollment.DoesNotExist:
            messages.error(
                self.request,
                "You are not enrolled in this semester!",
            )
            return redirect("/")

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
                "That attendance code is not currently valid. Your attendance was not recorded.",
            )

        return super().form_valid(form)


@login_required
def manually_add_or_verify_attendance(request):
    if request.method == "POST":
        user = (
            User.objects.get(pk=request.POST["user"])
            if request.POST.get("user")
            else User.objects.get(rcs_id=request.POST["rcs_id"])
        )
        meeting = Meeting.objects.get(pk=request.POST["meeting"])

        if (
            not request.user.is_mentor(meeting.semester)
            and not request.user.is_superuser
        ):
            return redirect(reverse("meetings_index"))

        try:
            attendance = MeetingAttendance.objects.get(user=user, meeting=meeting)
            if not attendance.is_verified:
                attendance.is_verified = True
                messages.info(request, "Verified attendance")
        except MeetingAttendance.DoesNotExist:
            attendance = MeetingAttendance(
                meeting=meeting, user=user, is_verified=True, is_added_by_admin=True
            )
            messages.success(request, "Added attendance.")
        attendance.save()

        return redirect(reverse("meetings_detail", args=(meeting.pk,)))
    return redirect(reverse("meetings_index"))
