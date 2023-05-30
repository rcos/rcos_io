"""This module contains checks that can be run for a given user and a given semester."""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, TypedDict
from portal.models import Enrollment, MentorApplication, Semester, User
from collections.abc import Callable
from django.utils import timezone
from django.apps import apps


class FailedCheck(Exception):
    """A failed check with a reason and possible fix."""

    reason: str
    fix: Optional[str]

    def __init__(self, reason: str, fix: Optional[str] = None) -> None:
        self.reason = reason
        self.fix = fix
        super().__init__(reason)


@dataclass
class CheckResult:
    """The result of a check."""

    passed: bool
    fail_reason: str = ""
    fix: str = ""

    def __bool__(self):
        return self.passed

    def __str__(self):
        display_str = self.fail_reason
        if self.fix:
            display_str += " " + self.fix
        return display_str


class Check:
    dependencies: List["Check"] = []
    """The checks that will run before this one."""

    fail_reason: str
    """The fallback fail reason if this check fails."""

    fix: Optional[str] = None
    """The way for the user to pass this check (if applicable)."""

    def run(self, user: User, semester: Optional[Semester] = None):
        for dep in self.dependencies:
            dep.run(user, semester)

    def fail(self, fail_reason: Optional[str] = None, fix: Optional[str] = None):
        raise FailedCheck(fail_reason or self.fail_reason, fix)

    def check(self, user: User, semester: Optional[Semester]):
        try:
            self.run(user, semester)
            return CheckResult(passed=True, fail_reason="", fix="")
        except FailedCheck as e:
            return CheckResult(passed=False, fail_reason=e.reason, fix=e.fix or "")

    def passes(self, user: User, semester: Optional[Semester]):
        try:
            self.run(user, semester)
            return True
        except FailedCheck:
            return False


class CheckUserAuthenticated(Check):
    fail_reason = "You are not logged in."
    fix = "Login!"

    def run(self, user: User, semester: Optional[None] = None):
        super().run(user, semester)
        if not user.is_authenticated:
            self.fail()


class CheckSemesterActive(Check):
    def run(self, user: User, semester: Optional[Semester] = None):
        super().run(user, semester)

        if not semester:
            return self.fail("No semester found.")

        if not semester.is_active:
            self.fail("Semester is not active.")


class CheckUserApproved(Check):
    dependencies = [CheckUserAuthenticated()]
    fail_reason = "Your account has not yet been approved."
    fix = "Contact a Coordinator/Faculty Advisor to verify your identity."

    def run(self, user: User, semester: Optional[Semester] = None):
        super().run(user, semester)
        if not user.is_approved:
            self.fail()


class CheckUserSetup(Check):
    dependencies = [CheckUserApproved()]
    fail_reason = "You have not completed your profile."
    fix = "On the profile page, fill out your details and link your GitHub and Discord accounts."

    def run(self, user: User, semester: Semester | None):
        super().run(user, semester)
        missing = []
        if not user.first_name:
            missing.append("first name")
        if not user.last_name:
            missing.append("last name")
        if not user.discord_user_id:
            missing.append("Discord account")
        if not user.github_username:
            missing.append("GitHub account")
        if len(missing) > 0:
            self.fail(
                self.fail_reason,
                "On the profile page, enter your " + ", ".join(missing) + ".",
            )


class CheckUserRPI(Check):
    dependencies = [CheckUserApproved()]
    fail_reason = "You are not an approved RPI student/faculty."

    def run(self, user: User, semester: Optional[None] = None):
        super().run(user, semester)
        if not user.role == User.RPI:
            self.fail()


class CheckBeforeSemesterDeadline(Check):
    def __init__(self, deadline_key: str, deadline_name: str) -> None:
        super().__init__()
        self.deadline_key = deadline_key
        self.deadline_name = deadline_name

    def run(self, user: User, semester: Optional[None] = None):
        super().run(user, semester)

        try:
            deadline: datetime | None = getattr(semester, self.deadline_key)
        except KeyError:
            return self.fail("Deadline not recognized.")

        if deadline is not None:
            now = timezone.now()
            if now > deadline:
                self.fail(
                    f"The {self.deadline_name} deadline ({deadline.strftime('%-m/%-d %-I:%M %p')}) has passed."
                )


class CheckUserCanEnroll(Check):
    dependencies = [
        CheckUserSetup(),
        CheckSemesterActive(),
        CheckBeforeSemesterDeadline("enrollment_deadline", "enrollment"),
    ]


class CheckUserCanProposeProject(Check):
    dependencies = [
        CheckUserSetup(),
        CheckSemesterActive(),
        CheckBeforeSemesterDeadline("project_pitch_deadline", "project pitch"),
    ]
    fail_reason = "You are not eligible to propose projects at this time."

    def run(self, user: User, semester: Semester):
        super().run(user, semester)

        if user.owned_projects.filter(is_approved=False).count() > 0:
            return self.fail("You have an unapproved project pending.")

        try:
            if Enrollment.objects.get(user=user, semester=semester).project:
                return self.fail("You're already enrolled on a project this semester.")
        except Enrollment.DoesNotExist:
            pass


class CheckUserCanApplyAsMentor(Check):
    dependencies = [
        CheckUserSetup(),
        CheckUserRPI(),
        CheckSemesterActive(),
        CheckBeforeSemesterDeadline(
            "mentor_application_deadline", "mentor application"
        ),
    ]

    def run(self, user: User, semester: Semester):
        super().run(user, semester)

        try:
            if MentorApplication.objects.get(user=user, semester=semester):
                return self.fail("You already applied to be a Mentor this semester.")
        except MentorApplication.DoesNotExist:
            pass
