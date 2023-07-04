"""This module contains checks that can be run for a given user and a given semester."""

from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from portal.models import Enrollment, MentorApplication, Project, Semester, User


class FailedCheck(Exception):
    """A failed check with a reason and possible fix."""

    reason: str
    fix: str | None

    def __init__(self, reason: str, fix: str | None = None) -> None:
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
    dependencies: list["Check"] = []
    """The checks that will run before this one."""

    fail_reason: str
    """The fallback fail reason if this check fails."""

    fix: str | None = None
    """The way for the user to pass this check (if applicable)."""

    def run(
        self,
        user: User,
        semester: Semester | None = None,
        project: Project | None = None,
    ):
        for dep in self.dependencies:
            dep.run(user, semester, project)

    def fail(self, fail_reason: str | None = None, fix: str | None = None):
        raise FailedCheck(fail_reason or self.fail_reason, fix)

    def check(
        self,
        user: User,
        semester: Semester | None = None,
        project: Project | None = None,
    ):
        try:
            self.run(user, semester, project)
            return CheckResult(passed=True, fail_reason="", fix="")
        except FailedCheck as e:
            return CheckResult(passed=False, fail_reason=e.reason, fix=e.fix or "")

    def passes(self, user: User, semester: Semester | None, project: Project | None):
        try:
            self.run(user, semester, project)
            return True
        except FailedCheck:
            return False


class CheckUserAuthenticated(Check):
    fail_reason = "You are not logged in."
    fix = "Login!"

    def run(
        self,
        user: User,
        semester: Semester | None = None,
        project: Project | None = None,
    ):
        super().run(user, semester, project)
        if not user.is_authenticated:
            self.fail()


class CheckSemesterActive(Check):
    def run(
        self,
        user: User,
        semester: Semester | None = None,
        project: Project | None = None,
    ):
        super().run(user, semester, project)

        if not semester:
            return self.fail("No semester found.")

        if not semester.is_active:
            self.fail("Semester is not active.")


class CheckUserApproved(Check):
    dependencies = [CheckUserAuthenticated()]
    fail_reason = "Your account has not yet been approved."
    fix = "Contact a Coordinator/Faculty Advisor to verify your identity."

    def run(
        self,
        user: User,
        semester: Semester | None = None,
        project: Project | None = None,
    ):
        super().run(user, semester, project)
        if not user.is_approved:
            self.fail()


class CheckUserSetup(Check):
    dependencies = [CheckUserApproved()]
    fail_reason = "You have not completed your profile."
    fix = "On the profile page, fill out your details and link your GitHub and Discord accounts."

    def run(self, user: User, semester: Semester | None, project: Project | None):
        super().run(user, semester, project)
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

    def run(
        self,
        user: User,
        semester: Semester | None = None,
        project: Project | None = None,
    ):
        super().run(user, semester, project)
        if not user.role == User.RPI:
            self.fail()


class CheckBeforeSemesterDeadline(Check):
    def __init__(self, deadline_key: str, deadline_name: str) -> None:
        super().__init__()
        self.deadline_key = deadline_key
        self.deadline_name = deadline_name

    def run(
        self,
        user: User,
        semester: Semester | None = None,
        project: Project | None = None,
    ):
        super().run(user, semester, project)

        try:
            deadline: datetime | None = getattr(semester, self.deadline_key)
        except KeyError:
            return self.fail("Deadline not recognized.")

        if deadline is not None:
            now = timezone.now()
            if now > deadline:
                self.fail(
                    f"The {self.deadline_name} deadline "
                    f"({deadline.strftime('%-m/%-d %-I:%M %p')}) has passed."
                )


class CheckUserCanEnroll(Check):
    dependencies = [
        CheckUserSetup(),
        CheckSemesterActive(),
        CheckBeforeSemesterDeadline("enrollment_deadline", "enrollment"),
    ]


class CheckUserNotAlreadyEnrolled(Check):
    dependencies = [CheckSemesterActive()]
    fail_reason = "You're already enrolled on a project this semester."

    def run(
        self,
        user: User,
        semester: Semester | None = None,
        project: Project | None = None,
    ):
        super().run(user, semester, project)

        if user.owned_projects.filter(is_approved=False).count() > 0:
            return self.fail("You have an unapproved project pending.")

        try:
            if Enrollment.objects.get(user=user, semester=semester).project:
                return self.fail()
        except Enrollment.DoesNotExist:
            pass


class CheckUserCanCreateProject(Check):
    dependencies = [
        CheckUserSetup(),
        CheckSemesterActive(),
        CheckUserNotAlreadyEnrolled(),
        CheckBeforeSemesterDeadline("project_pitch_deadline", "project pitch"),
    ]
    fail_reason = "You are not eligible to create projects at this time."


class CheckUserIsProjectLeadOrOwner(Check):
    def run(
        self,
        user: User,
        semester: Semester,
        project: Project | None = None,
    ):
        super().run(user, semester, project)

        enrollment = Enrollment.objects.get(user=user, semester=semester)

        if not enrollment:
            return self.fail(f"You are not enrolled for {semester}.")

        if not project:
            return self.fail(f"You are not enrolled on a project for {semester}.")

        if not project.owner == user and not (
            enrollment.project == project and enrollment.is_project_lead
        ):
            return self.fail(
                f"You are not the owner or a current project lead of {project} for {semester}."
            )


class CheckUserCanPitchProject(Check):
    dependencies = [
        CheckUserSetup(),
        CheckSemesterActive(),
        CheckBeforeSemesterDeadline("project_pitch_deadline", "project pitch"),
        CheckUserIsProjectLeadOrOwner(),
    ]

class CheckUserCanSubmitProjectProposal(Check):
    dependencies = [
        CheckUserSetup(),
        CheckSemesterActive(),
        CheckBeforeSemesterDeadline("project_proposal_deadline", "project proposal"),
        CheckUserIsProjectLeadOrOwner(),
    ]


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
        super().run(user, semester, project)

        try:
            if MentorApplication.objects.get(user=user, semester=semester):
                return self.fail("You already applied to be a Mentor this semester.")
        except MentorApplication.DoesNotExist:
            pass
