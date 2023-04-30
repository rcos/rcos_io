import csv
import logging
import random
import re
import string
from typing import Any, Dict, Optional, cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView
from django.views.generic.edit import FormView
from sentry_sdk import capture_exception, capture_message
from django.db.models import Q

from portal.forms import SubmitAttendanceForm
from portal.views import UserRequiresSetupMixin
from portal.views.admin import is_admin

from ..models import (
    Enrollment,
    Meeting,
    MeetingAttendance,
    MeetingAttendanceCode,
    Semester,
    SmallGroup,
    User,
)

logger = logging.getLogger(__name__)


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

    # Fetch 10 most recent published meetings, calendar will fetch all from API separately
    def get_queryset(self):
        now = timezone.now()

        upcoming = (
            Meeting.get_user_queryset(self.request.user)
            .filter(starts_at__gte=now)
            .order_by("starts_at")
            .select_related()[:10]
        )

        ongoing = (
            Meeting.get_user_queryset(self.request.user)
            .filter(starts_at__lte=now)
            .filter(ends_at__gte=now)
            .order_by("starts_at")
            .select_related()[:10]
        )

        queryset = {"ongoing": ongoing, "upcoming": upcoming}

        return queryset


class MeetingDetailView(DetailView):
    object: Meeting
    small_group: Optional[SmallGroup]
    template_name = "portal/meetings/detail.html"
    model = Meeting
    context_object_name = "meeting"

    def can_manage_attendance(self):
        if not self.request.user.is_authenticated:
            return False

        active_enrollment = self.request.user.enrollments.filter(
            semester_id=self.object.semester_id
        ).first()

        if self.request.user.is_superuser:
            return True

        # Mentors can manage general meeting attendance except mentor and coordinator meetings
        if (
            active_enrollment
            and active_enrollment.is_mentor
            and self.object.type not in (Meeting.MENTOR, Meeting.COORDINATOR)
        ):
            return True

        # Meeting hosts also can manage attendance
        if self.object.host == self.request.user:
            return True

        return False

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

        can_manage_attendance = cache.get_or_set(
            f"can_manage_attendance:{self.object.pk}:{self.request.user.pk}",
            default=self.can_manage_attendance,
            timeout=60 * 60 * 24,
        )

        if can_manage_attendance:
            data["can_manage_attendance"] = True

            if self.request.user.is_superuser:
                data["small_groups"] = SmallGroup.objects.all()
            else:
                data["small_groups"] = self.request.user.mentored_small_groups.filter(
                    semester_id=self.object.semester_id
                )

            small_group_pk = self.request.GET.get("small_group")
            small_group = None
            if small_group_pk:
                small_group = SmallGroup.objects.get(pk=small_group_pk)
                data["target_small_group"] = small_group

            query = {}
            if small_group:
                query["small_group"] = small_group
            else:
                query["small_group__isnull"] = True

            def get_or_create_attendance_code():
                try:
                    code, is_code_new = self.object.attendance_codes.get_or_create(
                        **query,
                        defaults={"code": generate_code(), "small_group": small_group},
                    )
                except MeetingAttendanceCode.MultipleObjectsReturned as err:
                    logger.warning(
                        f"Two or more global attendance codes found for meeting {self.object.pk}"
                    )
                    capture_exception(err)

                    code = (
                        self.object.attendance_codes.filter(**query)
                        .order_by("code")
                        .first()
                    )
                return code

            if self.object.is_ongoing:
                code = cache.get_or_set(
                    f"attendance_codes:{self.object.pk}:{small_group.pk if small_group else 'none'}",
                    default=get_or_create_attendance_code,
                    timeout=60 * 30,
                )
            else:
                code = None

            data["code"] = code

            if self.request.user.is_superuser:
                data["small_group_attendance_ratios"] = cache.get_or_set(
                    f"small_group_attendance_ratios:{self.object.pk}",
                    self.object.get_small_group_attendance_ratios,
                    60 * 30,
                )

            data = {
                **data,
                **self.object.get_attendance_data(small_group),
            }

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
                    "That is not your Small Group's attendance code... Nice try. If we're wrong about this, let your Mentor know immediately!",
                )
                capture_message(
                    f"User {self.request.user} submitted attendance code {meeting_attendance_code} for meeting {meeting_attendance_code.meeting} from wrong Small Group"
                )
                return redirect(reverse("submit_attendance"))

            new_attendance = MeetingAttendance(
                meeting=meeting_attendance_code.meeting,
                user=user,
                is_verified=random.random()
                > meeting_attendance_code.meeting.attendance_chance_verification_required,
            )

            # If the user has previously failed verification, require verification
            # until they get explicitly verified.
            # This cache key is cleared when a Mentor verifies them.
            if cache.has_key(f"failed-verification:{user.pk}"):
                new_attendance.is_verified = False

            try:
                new_attendance.save()
            except IntegrityError:
                messages.warning(
                    self.request,
                    "You've already submitted attendance for this meeting!",
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
        small_group_id = request.POST.get("small_group", None)

        action = request.POST.get("action", "accept")

        if action not in ["accept", "deny"]:
            messages.error(request, "Action not understood.")
            return redirect(reverse("meetings_detail", args=(meeting.pk,)))

        user_ids = [
            s.strip() for s in re.split(r',|;|\s', request.POST.get("user", ""))
            if s.strip()
        ]

        # Split RCS IDs on whitespaces, commands, semicolons, and remove parentheses
        rcs_ids = [
            re.sub(r'\(|\)', '', s.strip()) for s in re.split(r',|;|\s', request.POST.get("rcs_id", ""))
            if s.strip()
        ]

        if not user_ids and not rcs_ids:
            messages.warning(request, "You did not enter a user ID or RCS ID!")
            return redirect(reverse("meetings_detail", args=(meeting.pk,)))

        if user_ids:
            users = User.objects.filter(pk__in=user_ids)
        else:
            users = User.objects.filter(rcs_id__in=rcs_ids)

        for user in users:
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
            
            if action == "accept":
                try:
                    attendance = MeetingAttendance.objects.get(user=user, meeting=meeting)
                    if not attendance.is_verified:
                        attendance.is_verified = True
                        attendance.save()

                        # Clear the cache of any record of this person previously failing verification
                        cache.delete(f"failed-verification:{user.pk}")
                except MeetingAttendance.DoesNotExist:
                    attendance = MeetingAttendance(
                        meeting=meeting,
                        user=user,
                        is_verified=True,
                        is_added_by_admin=True
                    )
                    attendance.save()
                    messages.success(request, f"Added attendance for {user}!")

                # Submit attendance for submitter themselves
                try:
                    MeetingAttendance(user=request.user, meeting=meeting).save()
                except IntegrityError:
                    pass
            elif action == "deny":
                cache.set(
                    f"failed-verification:{user.pk}", 1, 60 * 60 * 24 * 30 * 3
                )  # 3 months
                MeetingAttendance.objects.filter(user=user, meeting=meeting).delete()

        return redirect(
            reverse("meetings_detail", args=(meeting.pk,))
            + ("?small_group=" + small_group_id if small_group_id else "")
            + "#attendance"
        )

    return redirect(reverse("meetings_index"))


@login_required
def user_attendance(request: HttpRequest, pk: Any):
    target_user = cast(User, User.objects.get(pk=pk))

    if not request.user.is_superuser and target_user != request.user:
        return HttpResponseForbidden()

    # Fetch the desired semester
    try:
        target_semester = Semester.objects.get(pk=request.GET["semester"])
    except Semester.DoesNotExist:
        messages.error(request, "No such semester found.")
        return redirect(reverse("users_detail", args=(target_user.pk,)))

    # Fetch target user's meeting attendance along with the meetings they *should* be attending
    user_expected_meetings = target_user.get_expected_meetings(target_semester)
    user_attendances = MeetingAttendance.objects.filter(
        user=target_user, meeting__in=user_expected_meetings
    )

    # Counts
    group_meetings_total = 0
    group_meetings_attended = 0
    workshops_total = 0
    workshops_attended = 0

    # Connect meetings with the user's attendances to display in a table
    expected_meetings_rows = []
    for meeting in user_expected_meetings:
        meeting: Meeting
        row = {
            "meeting": meeting,
            "attendance": next(
                (ua for ua in user_attendances if ua.meeting_id == meeting.pk), None
            ),
        }

        # Increment counts
        if meeting.is_attendance_taken:
            if (
                meeting.type == Meeting.SMALL_GROUP
                or meeting.type == Meeting.LARGE_GROUP
            ):
                group_meetings_total += 1
            elif meeting.type == Meeting.WORKSHOP:
                workshops_total += 1

            if row["attendance"] and row["attendance"].is_verified:
                if (
                    meeting.type == Meeting.SMALL_GROUP
                    or meeting.type == Meeting.LARGE_GROUP
                ):
                    group_meetings_attended += 1
                elif meeting.type == Meeting.WORKSHOP:
                    workshops_attended += 1

        expected_meetings_rows.append(row)

    return render(
        request,
        "portal/meetings/attendance/index.html",
        {
            "target_user": target_user,
            "target_semester": target_semester,
            "expected_meetings_rows": expected_meetings_rows,
            "group_meetings_total": group_meetings_total,
            "group_meetings_attended": group_meetings_attended,
            "workshops_total": workshops_total,
            "workshops_attended": workshops_attended,
        },
    )

@login_required
@user_passes_test(is_admin)
def export_meeting_attendance(request, pk: Any):
    meeting = get_object_or_404(Meeting, pk=pk)
    
    filename = "RCOS " + str(meeting) + " Attendance"

    # Set the appropriate response headers so the browser expects a CSV file download
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{filename}.csv"'},
    )

    # Create a CSV writer that writes to the response
    writer = csv.writer(response)

    # Write the headers
    writer.writerow(['user id', 'given name', 'family name', 'grade1', 'totalgrade'])

    # Iterate through every **verified** attendance and write a CSV row
    for user in meeting.attendances.filter(meetingattendance__is_verified=True):
        writer.writerow([user.rcs_id, user.first_name, user.last_name, 1, 1])

    return response