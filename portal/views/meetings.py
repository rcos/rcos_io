import random
import string
from typing import Any, Dict
from django.db import IntegrityError
from django.core.cache import cache

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView

from portal.forms import SubmitAttendanceForm
from portal.views import UserRequiresSetupMixin

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
        now = timezone.now()

        queryset = (
            Meeting.get_user_queryset(self.request.user)
            .filter(ends_at__gte=now)
            .select_related()[:5]
        )
        return queryset


class MeetingDetailView(DetailView):
    object: Meeting
    template_name = "portal/meetings/detail.html"
    model = Meeting
    context_object_name = "meeting"

    def can_manage_attendance(self):
        if not self.request.user.is_authenticated:
            return None, False

        active_enrollment = self.request.user.enrollments.filter(
            semester_id=self.object.semester_id
        ).first()

        if self.request.user.is_superuser:
            return active_enrollment, True

        # Mentors can manage general meeting attendance except mentor and coordinator meetings
        if (
            active_enrollment
            and active_enrollment.is_mentor
            and self.object.type not in (Meeting.MENTOR, Meeting.COORDINATOR)
        ):
            return active_enrollment, True

        # Meeting hosts also can manage attendance
        if self.object.host == self.request.user:
            return active_enrollment, True

        return active_enrollment, False

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)

        # Check attendance status
        if self.request.user.is_authenticated and self.request.user.is_rpi:
            try:
                data["user_attendance"] = MeetingAttendance.objects.get(
                    meeting=self.object, user=self.request.user
                )
            except MeetingAttendance.DoesNotExist:
                data["user_attendance"] = None

            data["submit_attendance_form"] = SubmitAttendanceForm()
        else:
            data["submit_attendance_form"] = None

        data["can_manage_attendance"] = False
        active_enrollment, can_manage_attendance = self.can_manage_attendance()
        data["active_enrollment"] = active_enrollment
        if can_manage_attendance:
            data["can_manage_attendance"] = True

            expected_users = self.object.expected_attendance_users
            attended_users = self.object.attended_users

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
            data["expected_users"] = expected_users
            data["attendance_ratio"] = (
                attended_users.count() / expected_users.count()
                if expected_users.count() > 0
                else 0
            )

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


def meetings_api(request):
    start, end = request.GET.get("start"), request.GET.get("end")

    meetings = Meeting.get_user_queryset(request.user).filter(
        starts_at__range=[start, end]
    )

    events = list(map(meeting_to_event, meetings))
    return JsonResponse(events, safe=False)


class SubmitAttendanceFormView(LoginRequiredMixin, UserRequiresSetupMixin, FormView):
    template_name = "portal/meetings/attendance/submit.html"
    form_class = SubmitAttendanceForm
    success_url = "/meetings"

    def form_valid(self, form: SubmitAttendanceForm):
        code = form.cleaned_data["code"]
        user = self.request.user

        # Search for attendance code
        try:
            meeting_attendance_code = MeetingAttendanceCode.objects.select_related(
                "meeting", "small_group"
            ).get(pk__iexact=code)
        except MeetingAttendanceCode.DoesNotExist:
            messages.error(
                self.request,
                "Attendance code not recognized. Your attendance was not recorded.",
            )
            return super().form_valid(form)

        user.enrollments.get_or_create(
            semester_id=meeting_attendance_code.meeting.semester_id
        )

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
                return redirect(reverse("submit_attendance"))

            new_attendance = MeetingAttendance(
                meeting=meeting_attendance_code.meeting,
                user=user,
                is_verified=random.random()
                > meeting_attendance_code.meeting.attendance_chance_verification_required,
            )

            try:
                new_attendance.save()
            except IntegrityError:
                messages.warning(
                    self.request,
                    f"You've already submitted attendance for this meeting!",
                )
                return redirect(reverse("submit_attendance"))

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

        return redirect(meeting_attendance_code.meeting.get_absolute_url())


@login_required
def manually_add_or_verify_attendance(request):
    if request.method == "POST":
        meeting: Meeting = Meeting.objects.get(pk=request.POST["meeting"])

        user_id = request.POST.get("user", "").strip()
        rcs_id = request.POST.get("rcs_id", "").strip()

        if not user_id and not rcs_id:
            messages.warning(request, "You did not enter a user ID or RCS ID!")
            return redirect(reverse("meetings_detail", args=(meeting.pk,)))

        try:
            user = (
                User.objects.get(pk=user_id)
                if user_id
                else User.objects.get(rcs_id=rcs_id)
            )
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect(reverse("meetings_detail", args=(meeting.pk,)))

        try:
            submitter_enrollment = request.user.enrollments.get(
                semester=meeting.semester
            )
            if (
                not request.user.is_superuser
                and not submitter_enrollment.is_faculty_advisor
                and not submitter_enrollment.is_coordinator
                and not submitter_enrollment.is_mentor
            ):
                return redirect(reverse("meetings_index"))

            if (
                not request.user.is_superuser
                and not submitter_enrollment.is_coordinator
                and submitter_enrollment.is_mentor
                and meeting.type == Meeting.MENTOR
            ):
                messages.warning(
                    request,
                    "You cannot manually submit attendance for a Mentor meeting!",
                )
                return redirect(reverse("meetings_detail", args=(meeting.pk,)))
        except Enrollment.DoesNotExist:
            if not request.user.is_superuser:
                messages.error(
                    request,
                    "You must be an enrolled Faculty Advisor/Coordinator/Mentor to perform this action.",
                )
                return redirect(reverse("meetings_detail", args=(meeting.pk,)))

        user.enrollments.get_or_create(semester_id=meeting.semester_id)

        try:
            attendance = MeetingAttendance.objects.get(user=user, meeting=meeting)
            if not attendance.is_verified:
                attendance.is_verified = True
                attendance.save()
                messages.info(request, f"Verified attendance for {user}.")
        except MeetingAttendance.DoesNotExist:
            attendance = MeetingAttendance(
                meeting=meeting, user=user, is_verified=True, is_added_by_admin=True
            )
            attendance.save()
            messages.success(request, f"Added attendance for {user}!")

        return redirect(reverse("meetings_detail", args=(meeting.pk,)))
    return redirect(reverse("meetings_index"))
