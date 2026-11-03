from datetime import timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from portal.models import (
    ATTENDANCE_CODE_GRACE_PERIOD,
    Meeting,
    MeetingAttendanceCode,
)


def make_meeting(starts_in: timedelta, length: timedelta = timedelta(hours=1)):
    starts_at = timezone.now() + starts_in
    return Meeting(semester_id="test", starts_at=starts_at, ends_at=starts_at + length)


class AttendanceCodeValidityTests(SimpleTestCase):
    def assert_accepts(self, meeting: Meeting, expected: bool):
        self.assertEqual(meeting.is_accepting_attendance_codes, expected)
        self.assertEqual(
            MeetingAttendanceCode(code="ABCDE", meeting=meeting).is_valid, expected
        )

    def test_not_accepted_before_meeting_starts(self):
        self.assert_accepts(make_meeting(starts_in=timedelta(minutes=5)), False)

    def test_accepted_during_meeting(self):
        self.assert_accepts(make_meeting(starts_in=-timedelta(minutes=5)), True)

    def test_accepted_during_grace_period_after_meeting_ends(self):
        meeting = make_meeting(
            starts_in=-(timedelta(hours=1) + ATTENDANCE_CODE_GRACE_PERIOD / 2)
        )
        self.assertTrue(meeting.is_over)
        self.assert_accepts(meeting, True)

    def test_not_accepted_after_grace_period(self):
        meeting = make_meeting(
            starts_in=-(
                timedelta(hours=1) + ATTENDANCE_CODE_GRACE_PERIOD + timedelta(minutes=1)
            )
        )
        self.assert_accepts(meeting, False)
