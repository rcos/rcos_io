import logging
import re
from decimal import Decimal
from time import sleep
from typing import Optional, Tuple
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import formats, timezone
from requests import HTTPError
from sentry_sdk import capture_exception

from portal.services import discord

logger = logging.getLogger(__name__)


def sync_discord(sender, instance, created, *args, **kwargs):
    instance.sync_discord()


def sync_discord_on_delete(sender, instance, *args, **kwargs):
    instance.sync_discord(is_deleted=True)


@dataclass
class Eligibility:
    is_eligible: bool
    reason: Optional[str]

    @staticmethod
    def ineligible(reason: str):
        return Eligibility(False, reason)

    @staticmethod
    def eligible():
        return Eligibility(True, None)


class TimestampedModel(models.Model):
    """A base model that all other models should inherit from. It adds timestamps for creation and updating."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Room(TimestampedModel):
    """
    Represents a physical room on campus that events/small group meetings
    can be held in."
    """

    building = models.CharField(max_length=100)
    room = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.building} {self.room}"


class Semester(TimestampedModel):
    """Represents an RPI semeseter that RCOS takes place during."""

    id = models.CharField(
        max_length=len("202201"),
        primary_key=True,
        help_text="The unique ID of the semseter in RPI's format of YYYYMM where YYYY is the starting year and MM is the starting month.",
    )
    name = models.CharField(
        max_length=30, help_text="User-facing name of semester, e.g. Fall 2024"
    )

    mentor_application_deadline = models.DateTimeField(
        help_text="The last date students can apply to be Mentors for this semester",
        blank=True,
        null=True,
    )
    enrollment_deadline = models.DateTimeField(
        help_text="The last date users can enroll in the semester (not with a project yet)",
        blank=True,
        null=True,
    )
    project_enrollment_application_deadline = models.DateTimeField(
        help_text="The last date users can apply to a project",
        blank=True,
        null=True,
    )
    project_pitch_deadline = models.DateTimeField(
        help_text="The last date users can pitch a project",
        blank=True,
        null=True,
    )
    project_proposal_deadline = models.DateTimeField(
        blank=True,
        null=True,
    )

    start_date = models.DateField(
        "first day",
        help_text="The first day of the semester according to the RPI Academic Calendar: https://info.rpi.edu/registrar/academic-calendar",
    )
    end_date = models.DateField(
        "last day",
        help_text="The last day of the semester according to the RPI Academic Calendar: https://info.rpi.edu/registrar/academic-calendar",
    )

    rooms = models.ManyToManyField(Room, related_name="semesters", blank=True)

    @property
    def projects(self):
        return Project.objects.filter(enrollments__semester_id=self.pk).distinct()

    @classmethod
    def get_active(cls):
        """Returns the currently ongoing semester or `None` if none exists."""
        now = timezone.now().date()
        return cls.objects.filter(start_date__lte=now, end_date__gte=now).first()

    @classmethod
    def get_next(cls):
        """Returns the closest semester that hasn't started yet."""
        now = timezone.now().date()
        return cls.objects.filter(start_date__gte=now).order_by("start_date").first()

    @property
    def enrollment_count(self):
        return self.enrollments.count()

    @property
    def project_count(self):
        return self.enrollments.values("project").distinct().count()

    @property
    def is_active(self):
        now = timezone.now().date()
        return self.start_date <= now <= self.end_date

    def get_admins(self):
        return self.enrollments.filter(
            Q(is_coordinator=True) | Q(is_faculty_advisor=True)
        ).order_by("is_faculty_advisor")

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["start_date"]),
            models.Index(fields=["start_date", "end_date"]),
        ]


class Organization(TimestampedModel):
    """Represents an external organization that users and projects can belong to."""

    name = models.CharField(max_length=100, unique=True)
    email_domain = models.CharField(
        max_length=100,
        blank=True,
        help_text="The email domain used to auto-associate users to this org.",
    )
    email_domain_secondary = models.CharField(
        max_length=100,
        blank=True,
        help_text="A secondary email domain used to auto-associate users to this org.",
    )
    homepage_url = models.URLField(
        max_length=200, help_text="The public homepage of the organization."
    )
    discord_role_id = models.CharField(max_length=100, blank=True)

    def sync_discord(self, is_deleted=False):
        """Ensures that a Discord role exists for the organization, and that all its members have it assigned."""

        # Ensure existence of role
        # TODO: if role ID is set, check that is still exists and recreate if not
        if not self.discord_role_id:
            role = discord.create_role(
                {"name": self.name, "hoist": True, "mentionable": True}
            )
            self.discord_role_id = role["id"]
            self.save()

        # Add role to members
        for user in self.users:
            user: User
            if user.discord_user_id:
                discord.add_role_to_member(user.discord_user_id, self.discord_role_id)
                sleep(1)

    def __str__(self) -> str:
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class RPIUserManager(BaseUserManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(role=User.RPI, is_active=True, is_approved=True)
        )


class User(AbstractUser, TimestampedModel):
    """Represents an RCOS member, either an active RPI student/faculty with an RCS ID or an external user."""

    RPI = "rpi"
    EXTERNAL = "external"
    ROLE_CHOICES = ((RPI, "RPI"), (EXTERNAL, "External"))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    username = None
    email = models.EmailField("primary email address", unique=True)
    is_approved = models.BooleanField(
        "approved?",
        default=False,
        help_text="Identity is verified and can participate in RCOS",
    )
    role = models.CharField(choices=ROLE_CHOICES, max_length=30, default=EXTERNAL)

    organization = models.ForeignKey(
        Organization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
        help_text="The organization this user belongs to (optional)",
    )

    # Set for RPI users only
    rcs_id = models.CharField(
        blank=True,
        null=True,
        max_length=30,
        help_text="If the user is an RPI user, their RCS ID.",
        verbose_name="RCS ID",
        unique=True,
    )
    graduation_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="If the user is an RPI user, their graduation year.",
        validators=[MaxValueValidator(2028), MinValueValidator(1950)],
    )

    # Account integrations
    discord_user_id = models.CharField(
        blank=True,
        null=True,
        max_length=200,
        help_text="The user's Discord account ID from the Discord API",
        unique=True,
    )
    github_username = models.CharField(
        blank=True,
        null=True,
        max_length=200,
        help_text="The user's GitHub username (not user ID)",
        unique=True,
    )

    @property
    def is_rpi(self):
        return self.role == User.RPI

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or "Unnamed User"

    @property
    def display_name(self):
        """Returns a display name taking into account whatever parts of the user's profile is set."""
        chunks = []

        if self.first_name:
            chunks.append(self.first_name)
        if self.last_name:
            chunks.append(self.last_name[0])

        if self.role == User.RPI:
            if self.graduation_year:
                chunks.append(f"’{str(self.graduation_year)[2:]}")
            if len(chunks) > 0 and self.rcs_id:
                chunks.append(f"({self.rcs_id})")
            elif self.rcs_id:
                chunks.append(self.rcs_id)

        if len(chunks) == 0:
            chunks.append(self.email)

        return " ".join(chunks).strip()

    @property
    def is_setup(self):
        return (
            self.is_active
            and self.first_name
            and self.last_name
            and self.github_username
            and self.discord_user_id
        )

    def get_active_enrollment(self) -> Optional["Enrollment"]:
        active_semester = cache.get("active_semester")
        queryset = self.enrollments.filter(semester=active_semester)
        return queryset.first()

    def is_mentor(self, semester=None):
        if semester is None:
            active_enrollment = self.get_active_enrollment()
            return active_enrollment and active_enrollment.is_mentor

        return (
            self.enrollments.filter(
                is_mentor=True,
                semester=semester,
            ).count()
            > 0
        )

    def is_coordinator(self, semester=None):
        if semester is None:
            active_enrollment = self.get_active_enrollment()
            return active_enrollment and active_enrollment.is_coordinator

        return (
            self.enrollments.filter(
                is_coordinator=True,
                semester=semester,
            ).count()
            > 0
        )

    def is_faculty_advisor(self, semester=None):
        if semester is None:
            active_enrollment = self.get_active_enrollment()
            return active_enrollment and active_enrollment.is_faculty_advisor

        return (
            self.enrollments.filter(
                is_faculty_advisor=True,
                semester=semester,
            ).count()
            > 0
        )

    @property
    def discord_user(self):
        return discord.get_user(self.discord_user_id) if self.discord_user_id else None

    @property
    def discord_member(self):
        return (
            discord.get_server_member(self.discord_user_id)
            if self.discord_user_id
            else None
        )

    def send_message(self, message_content: str):
        """Send a direct message to the user via Discord. If Discord is not linked or it fails, sends an email."""

        sent = False
        if self.discord_user_id:
            try:
                dm_channel = discord.create_user_dm_channel(self.discord_user_id)
                discord.dm_user(dm_channel["id"], message_content)
                sent = True
            except Exception as e:
                capture_exception(e)

        if not sent:
            # Send backup email
            # TODO: send_mail
            pass

    def get_active_semesters(self):
        return (
            Semester.objects.filter(enrollments__user=self.id)
            .order_by("-start_date")
            .distinct()
        )

    # Permissions

    def can_enroll(self, semester: Semester) -> Eligibility:
        now = timezone.now()
        if semester.is_active and (
            semester.enrollment_deadline and now > semester.enrollment_deadline
        ):
            return Eligibility.ineligible("It is passed the enrollment deadline.")

        if not semester.is_active and semester != Semester.get_next():
            return Eligibility.ineligible(
                "There are no upcoming semesters in the system yet."
            )

        return Eligibility.eligible()

    def can_propose_project(self, semester: Optional[Semester]) -> Eligibility:
        if not self.is_approved or not self.is_active:
            return Eligibility.ineligible("Your account is not approved or active.")

        now = timezone.now()
        if not semester:
            return Eligibility.ineligible("No semester selected.")

        if not semester.is_active or (
            semester.project_pitch_deadline and now > semester.project_pitch_deadline
        ):
            return Eligibility.ineligible(
                "The current semester is not accepting new projects at this time.",
            )

        if self.owned_projects.filter(is_approved=False).count() > 0:
            return Eligibility.ineligible("You have an unapproved project pending.")

        try:
            if Enrollment.objects.get(user=self, semester=semester).project:
                return Eligibility.ineligible(
                    "You're already enrolled on a project this semester."
                )
        except Enrollment.DoesNotExist:
            pass

        return Eligibility.eligible()

    def can_apply_as_mentor(self, semester: Semester) -> Eligibility:
        if not self.is_approved or not self.is_active:
            return Eligibility.ineligible("Your account is not approved or active.")

        now = timezone.now()
        if not semester:
            return Eligibility.ineligible("No semester selected.")

        if not semester.is_active or (
            semester.project_pitch_deadline and now > semester.project_pitch_deadline
        ):
            return Eligibility.ineligible(
                "The current semester is not accepting new mentor applications at this time.",
            )

        try:
            if MentorApplication.objects.get(user=self, semester=semester):
                return Eligibility.ineligible("You already applied this semester.")
        except MentorApplication.DoesNotExist:
            pass

        return Eligibility.eligible()

    # End Permissions

    def get_expected_meetings(self, semester: Semester):
        # Determine what kinds of meetings this student is expected to attend
        meeting_types = [Meeting.LARGE_GROUP, Meeting.SMALL_GROUP, Meeting.WORKSHOP]
        return Meeting.objects.filter(type__in=meeting_types, semester=semester)

    def sync_discord(self, is_deleted=False):
        # Discord nickname and roles
        if self.discord_user_id:
            try:
                discord.set_member_nickname(self.discord_user_id, self.display_name)
                if self.is_approved:
                    discord.add_role_to_member(
                        self.discord_user_id, settings.DISCORD_VERIFIED_ROLE_ID
                    )
            except Exception as e:
                capture_exception(e)

    def get_absolute_url(self):
        return reverse("users_detail", args=[str(self.pk)])

    def __str__(self) -> str:
        return self.display_name

    objects = UserManager()
    rpi = RPIUserManager()

    def clean(self):
        if self.role != User.RPI and self.graduation_year is not None:
            raise ValidationError("Only RPI users can have a graduation year set.")

    class Meta:
        ordering = [Lower("first_name"), Lower("last_name")]
        indexes = [
            models.Index(fields=["is_approved"]),
            models.Index(fields=["email"]),
            models.Index(fields=["rcs_id"]),
            models.Index(fields=["first_name", "last_name"]),
        ]


def pre_save_user(instance, sender, *args, **kwargs):
    if instance._state.adding:
        if instance.email.endswith("@rpi.edu"):
            instance.role = User.RPI
            instance.is_approved = True
            instance.rcs_id = instance.email.removesuffix("@rpi.edu").lower()

        # Search for org with matching email domain
        email_domain = instance.email.split("@")[1]
        try:
            instance.organization = Organization.objects.get(
                Q(email_domain=email_domain) | Q(email_domain_secondary=email_domain)
            )
            instance.is_approved = True

            if instance.discord_user_id and instance.organization.discord_role_id:
                try:
                    discord.add_role_to_member(
                        instance.discord_user_id, instance.organization.discord_role_id
                    )
                except HTTPError as e:
                    capture_exception(e)
                    logger.exception(
                        f"Failed to add org Discord role for {instance.organization} to {instance}",
                        exc_info=e,
                    )
        except Organization.DoesNotExist:
            pass


# pre_save.connect(pre_save_user, sender=User)
# post_save.connect(sync_discord, sender=User)


class ProjectTag(TimestampedModel):
    """Represents a technology/language/framework/category/etc. that can be tagged to a project."""

    name = models.CharField(max_length=100, unique=True)

    def __str__(self) -> str:
        return self.name


class Project(TimestampedModel):
    """Represents an open source project in RCOS."""

    slug = models.SlugField()
    name = models.CharField(
        max_length=100, unique=True, help_text="The project's unique name"
    )
    owner = models.ForeignKey(
        User,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="owned_projects",
        help_text="The user that can edit the project",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        help_text="The external organization this project belongs to",
    )
    is_approved = models.BooleanField(
        "approved?",
        default=False,
        help_text="Whether the project has been approved by Mentors/Coordinators to participate in RCOS",
    )

    description = models.TextField(
        max_length=10_000, help_text="A description of the project", blank=True
    )

    external_chat_url = models.URLField(
        blank=True,
        help_text="Optional URL to an external chat that this project uses (e.g. a Discord invite link)",
    )

    homepage_url = models.URLField(
        blank=True,
        help_text="Optional URL to a homepage for the project, potentially where it is publicly deployed or to documentation",
    )

    logo_url = models.URLField(
        blank=True,
        help_text="Optional URL to a logo for the project",
    )

    tags = models.ManyToManyField(ProjectTag, blank=True, related_name="projects")

    discord_role_id = models.CharField(max_length=200, blank=True)

    discord_text_channel_id = models.CharField(max_length=200, blank=True)

    discord_voice_channel_id = models.CharField(max_length=200, blank=True)

    @property
    def discord_text_channel_url(self):
        if self.discord_text_channel_id:
            return f"https://discord.com/channels/{settings.DISCORD_SERVER_ID}/{self.discord_text_channel_id}"
        return None

    def send_discord_message(self, message_content: str):
        if self.discord_text_channel_id:
            discord.send_message(
                self.discord_text_channel_id, {"content": message_content}
            )

    def sync_discord(self, is_deleted=False):
        active_semester = Semester.get_active()

        if not active_semester:
            # TODO: delete all project channels except external ones?
            logger.warning(
                f"No active semester, deleting all Discord channels and roles for project {self}"
            )
            return

        # Determine if this project is running this semester
        enrollments = self.enrollments.filter(semester=active_semester).select_related(
            "user"
        )

        if len(enrollments) > 0:
            logger.info(
                f"{self} is an active project, upserting Discord channels and roles"
            )
            # An active project, ensure roles and channels exist
            if not self.discord_role_id:
                try:
                    project_role = discord.create_role(
                        {"name": self.name, "hoist": True, "mentionable": True}
                    )

                    self.discord_role_id = project_role["id"]
                    self.save()
                    sleep(1)
                except HTTPError as e:
                    capture_exception(e)
                    logger.exception(
                        f"Failed to create project Discord role for {self}", exc_info=e
                    )

            if self.discord_role_id:
                # Apply role to team members
                for enrollment in enrollments:
                    discord_user_id = enrollment.user.discord_user_id
                    if not discord_user_id:
                        logger.warning(
                            f"Skipping {enrollment.user} since no Discord linked"
                        )
                        continue

                    if enrollment.is_project_lead:
                        try:
                            discord.add_role_to_member(
                                discord_user_id, settings.DISCORD_PROJECT_LEAD_ROLE_ID
                            )
                            sleep(1)
                        except HTTPError as e:
                            capture_exception(e)
                            logger.exception(
                                f"Failed to add Project Lead role to {enrollment.user}",
                                exc_info=e,
                            )
                    try:
                        discord.add_role_to_member(
                            discord_user_id, self.discord_role_id
                        )
                        sleep(1)
                    except HTTPError as e:
                        capture_exception(e)
                        logger.exception(
                            f"Failed to add project Discord role for {self} to {enrollment.user}",
                            exc_info=e,
                        )
        else:
            # TODO: Not an active project, DESTROY EVERY TRACE OF IT
            logger.info(
                f"{self} is a UNACTIVE project, removing Discord channels and roles"
            )
            pass

        # Channels
        # text_channel_params = None
        # # Are small groups formed yet?
        # if SmallGroup.objects.filter(semester=semester).count() > 0:
        #     raise NotImplementedError
        # else:
        #     pitch = self.is_seeking_members(semester)
        #     if pitch:
        #         # No! This is early semester, only a text channel should exist and it should be under the
        #         # Project Pairing category

        #         lead_discord_mentions = " / ".join(
        #             [
        #                 (
        #                     f"<@{e.user.discord_user_id}>"
        #                     if e.user.discord_user_id
        #                     else e.user.display_name
        #                 )
        #                 for e in self.enrollments.filter(
        #                     semester=semester, is_project_lead=True
        #                 ).select_related("user")
        #             ]
        #         )

        #         repos = "Repositories:\n" + "\n".join(
        #             [r.url for r in self.repositories.all()]
        #         )
        #         text_channel_params = {
        #             "name": self.name,
        #             "type": discord.TEXT_CHANNEL_TYPE,
        #             "parent_id": settings.DISCORD_PROJECT_PAIRING_CATEGORY_ID,
        #             "topic": inspect.cleandoc(
        #                 f"""**{self.name}**

        #                 {self.description}

        #                 Project Lead(s): {lead_discord_mentions}

        #                 Pitch: {pitch.url}

        #                 {repos}

        #                 {settings.PUBLIC_BASE_URL + reverse("projects_detail", args=(self.pk,))}
        #                 """
        #             ),
        #         }

        # if text_channel_params:
        #     if self.discord_text_channel_id:
        #         try:
        #             text_channel = discord.modify_server_channel(
        #                 self.discord_text_channel_id,
        #                 cast(discord.ModifyChannelParams, text_channel_params),
        #             )
        #         except HTTPError as e:
        #             capture_exception(e)
        #             logger.exception(
        #                 f"Failed to update project Discord text channel for {self}",
        #                 exc_info=e,
        #             )
        #     else:
        #         try:
        #             text_channel = discord.create_server_channel(
        #                 cast(discord.CreateServerChannelParams, text_channel_params)
        #             )
        #             self.discord_text_channel_id = text_channel["id"]
        #             self.save()
        #         except HTTPError as e:
        #             capture_exception(e)
        #             logger.exception(
        #                 f"Failed to create project Discord text channel for {self}",
        #                 exc_info=e,
        #             )

    def get_active_semesters(self):
        return (
            Semester.objects.filter(enrollments__project=self.id)
            .order_by("-start_date")
            .distinct()
        )

    def get_absolute_url(self):
        return reverse("projects_detail", kwargs={"slug": self.slug})

    def is_seeking_members(self, semester: Semester) -> Optional["ProjectPitch"]:
        return self.pitches.filter(semester=semester, project=self).first()

    def save(self, *args, **kwargs):
        if not self.slug or self.slug != slugify(self.name):
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = [Lower("name")]
        get_latest_by = "created_at"
        indexes = [models.Index(fields=["name", "description"])]


# post_save.connect(sync_discord, sender=Project)


class ProjectRepository(TimestampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="repositories"
    )
    url = models.URLField(help_text="URL of GitHub repository")


class ProjectPitch(TimestampedModel):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="project_pitches"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="pitches"
    )
    url = models.URLField(
        "Presentation URL",
        help_text="Direct link to the pitch presentation (usually a Google Slides link)",
    )

    def __str__(self) -> str:
        return f"{self.semester} {self.project} Pitch: {self.url}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["semester", "project"], name="unique_semester_pitch"
            )
        ]


class ProjectProposal(TimestampedModel):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="project_proposals"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="proposals"
    )
    url = models.URLField(help_text="Link to the actual proposal document")

    grade = models.DecimalField(
        max_digits=3,
        null=True,
        blank=True,
        decimal_places=1,
        help_text="The grade assigned to this proposal",
    )
    grader = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="graded_project_proposals",
    )
    grader_comments = models.TextField(
        max_length=10000,
        blank=True,
        help_text="Optional comments from the grader",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["semester", "project"], name="unique_semester_proposal"
            )
        ]


class ProjectPresentation(TimestampedModel):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="project_presentations"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="presentations"
    )
    url = models.URLField(help_text="Link to the actual presentation")

    grade = models.DecimalField(
        max_digits=3,
        null=True,
        blank=True,
        decimal_places=1,
        help_text="The grade assigned to this presentation",
    )
    grader = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="graded_project_presentations",
    )
    grader_comments = models.TextField(
        max_length=10000,
        blank=True,
        help_text="Optional comments from the grader",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["semester", "project"], name="unique_semester_presentation"
            )
        ]


class ProjectEnrollmentApplication(TimestampedModel):
    """Represents an application from a student to join a project."""

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="project_enrollment_applications",
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="project_enrollment_applications"
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="enrollment_applications",
    )
    is_accepted = models.BooleanField(null=True, default=None)
    why = models.TextField(
        max_length=10000, help_text="Why you want to join the project?"
    )
    experience = models.TextField(
        max_length=10000,
        help_text="What prior knowledge/experience related to this project do you have?",
    )

    rejection_reason = models.CharField(
        max_length=200,
        blank=True,
        help_text="Why the project lead rejected the application",
    )

    def accept(self):
        """Approves the user's request to join this project. Enrolls the user to the project and marks as approved."""
        if self.is_accepted is not None:
            return

        # Mark as accepted
        self.is_accepted = True

        # Upsert enrollment
        Enrollment.objects.update_or_create(
            semester=self.semester, user=self.user, defaults={"project": self.project}
        )

        self.save()

        # Notify user
        self.user.send_message(
            f"🎉 You've been accepted onto the **{self.project}** team!"
        )

    def reject(self):
        if self.is_accepted is not None:
            return

        # Mark as denied
        self.is_accepted = False

        self.save()

        # Notify user
        self.user.send_message(
            f"⚠ **{self.project}** has decided to not move forward with your application for the following reason:\n{self.rejection_reason}!"
        )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["semester", "user"],
                condition=Q(is_accepted=True),
                name="unique_accepted_application",
            )
        ]


class Enrollment(TimestampedModel):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="enrollments"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="enrollments",
    )
    credits = models.IntegerField(
        default=0,
        help_text="How many course credits the user is participating in RCOS for this semester. 0 means just for experience.",
    )
    is_for_pay = models.BooleanField(
        "for pay?",
        default=False,
        help_text="Whether the user is participating in RCOS for pay instead of course credit",
    )
    is_project_lead = models.BooleanField("project lead?", default=False)
    is_coordinator = models.BooleanField("coordinator?", default=False)
    is_mentor = models.BooleanField("mentor?", default=False)
    is_faculty_advisor = models.BooleanField("faculty advisor?", default=False)

    final_grade = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        help_text="The user's final grade for this semester (if taken for credits)",
        null=True,
        blank=True,
    )

    notes_markdown = models.TextField(
        max_length=10000,
        blank=True,
        help_text="Private notes for admins about this user for this semester",
    )

    def sync_discord(self, is_deleted=False):
        pass

    def get_absolute_url(self):
        return (
            reverse("users_detail", args=[str(self.user_id)])
            + "?semester="
            + self.semester.id
        )

    def __str__(self) -> str:
        return f"{self.semester.name} - {self.user} - {self.project or 'No project'}"

    class Meta:
        indexes = [
            models.Index(fields=["user", "semester"]),
            models.Index(fields=["user"]),
            models.Index(fields=["semester"]),
            models.Index(fields=["semester", "project"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["semester", "user"], name="unique_semester_enrollment"
            )
        ]
        ordering = ["semester", "user__first_name"]
        get_latest_by = ["semester"]


# post_save.connect(sync_discord, sender=Enrollment)


class PublicManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_published=True)
            .exclude(type=Meeting.COORDINATOR)
            .exclude(type=Meeting.MENTOR)
        )


class Meeting(TimestampedModel):
    SMALL_GROUP = "small_group"
    LARGE_GROUP = "large_group"
    WORKSHOP = "workshop"
    MENTOR = "mentor"
    COORDINATOR = "coordinator"
    TYPE_CHOICES = (
        (SMALL_GROUP, "Small Group"),
        (LARGE_GROUP, "Large Group"),
        (WORKSHOP, "Workshop"),
        (MENTOR, "Mentor"),
        (COORDINATOR, "Coordinator"),
    )
    TYPE_COLORS = {
        SMALL_GROUP: "red",
        LARGE_GROUP: "blue",
        WORKSHOP: "gold",
        MENTOR: "purple",
        COORDINATOR: "orange",
    }

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="meetings",
        default=Semester.get_active,
    )
    name = models.CharField(
        max_length=100, blank=True, help_text="The optional title of the meeting"
    )
    host = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Optional host for the meeting (e.g. mentor hosting a workshop)",
    )
    type = models.CharField(choices=TYPE_CHOICES, max_length=100, default=SMALL_GROUP)
    is_published = models.BooleanField(
        "published?", default=False, help_text="Whether the meeting is visible to users"
    )
    is_attendance_taken = models.BooleanField(
        "attendance taken?",
        default=True,
        help_text="Whether attendance is taken at this meeting. If false, all expected users are counted as attended.",
    )
    starts_at = models.DateTimeField(help_text="When the meeting starts")
    ends_at = models.DateTimeField(help_text="When the meeting ends")
    location = models.CharField(
        max_length=500,
        blank=True,
        help_text="Where the meeting takes place either physically or virtually",
    )
    room = models.ForeignKey(Room, on_delete=models.RESTRICT, blank=True, null=True)
    description_markdown = models.TextField(
        max_length=10000,
        blank=True,
        help_text="Optional publicly displayed description for the meeting. Supports Markdown.",
    )

    presentation_url = models.URLField(
        blank=True,
        help_text="The URL to the meeting's slideshow presentation if exists",
    )

    recording_url = models.URLField(
        blank=True, help_text="The URL to the meeting's recording (optional)"
    )

    attendance_chance_verification_required = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal(0.25),
        help_text="The % chance that a student submitting attendance will have to be verified (as a decimal)",
    )

    discord_event_id = models.CharField(
        blank=True,
        max_length=len("759071349561491526") + 5,
        help_text="Automatically managed, do not touch!",
    )

    # Relationships
    attendances = models.ManyToManyField(
        User, through="MeetingAttendance", related_name="meeting_attendances"
    )

    objects = models.Manager()

    public = PublicManager()
    """Public meetings that can be displayed to all users (and not logged in users)"""

    @property
    def presentation_embed_url(self):
        # e.g. https://docs.google.com/presentation/d/1McqgFPrXd3efJty39ekgZpj2kVwapkY6iuU6zGFKuEA/edit#slide=id.g550345e1c6_0_74
        if (
            self.presentation_url
            and "docs.google.com/presentation/d" in self.presentation_url
        ):
            match = re.search(r"[-\w]{25,}", self.presentation_url)
            if match:
                presentation_id = match.group()
                return f"https://docs.google.com/presentation/d/{presentation_id}/embed"
        return None

    @property
    def display_name(self):
        return self.name or self.get_type_display()

    @property
    def color(self):
        return (
            Meeting.TYPE_COLORS[self.type]
            if self.type in Meeting.TYPE_COLORS
            else "grey"
        )

    @property
    def is_over(self):
        now = timezone.now()
        return self.ends_at < now

    @property
    def is_upcoming(self):
        now = timezone.now()
        return self.starts_at > now

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.starts_at < now < self.ends_at

    @property
    def expected_attendance_users(self):
        # Get expected users based on meeting type and desired small group
        if self.type == Meeting.COORDINATOR:
            expected_users = User.rpi.filter(
                Q(enrollments__semester=self.semester_id)
                & (
                    Q(enrollments__is_coordinator=True)
                    | Q(enrollments__is_faculty_advisor=True)
                )
            )
        elif self.type == Meeting.MENTOR:
            expected_users = User.rpi.filter(
                enrollments__semester=self.semester_id, enrollments__is_mentor=True
            )
        else:
            expected_users = User.rpi.filter(enrollments__semester=self.semester_id)
        return expected_users

    def get_attendance_data(self, small_group: Optional["SmallGroup"] = None):
        expected_users = self.expected_attendance_users

        query = {"meeting": self}

        if small_group:
            small_group_user_ids = (
                small_group.get_users().values_list("pk", flat=True)
                if small_group
                else None
            )
            expected_users = expected_users.filter(pk__in=small_group_user_ids)
            query["user__in"] = small_group_user_ids

        attendances = MeetingAttendance.objects.filter(**query).select_related("user")

        needs_verification_users = []
        attended_users = []
        for attendance in attendances:
            attendance: MeetingAttendance
            if attendance.is_verified:
                attended_users.append(attendance.user)
            else:
                needs_verification_users.append(attendance.user)

        attendance_submitted_users = attended_users + needs_verification_users
        non_attended_users = expected_users.exclude(
            pk__in=[u.pk for u in attendance_submitted_users]
        )

        return {
            "expected_users": expected_users,
            "needs_verification_users": needs_verification_users,
            "attended_users": attended_users,
            "non_attended_users": non_attended_users,
            "attendance_ratio": len(attended_users) / expected_users.count()
            if expected_users.count() > 0
            else 0,
        }

    def get_small_group_attendance_ratios(self):
        small_groups = {}
        for small_group in SmallGroup.objects.filter(semester_id=self.semester_id):
            attendance_data = self.get_attendance_data(small_group)
            small_groups[small_group.name] = attendance_data["attendance_ratio"]

        return small_groups

    @property
    def attended_users(self):
        return self.attendances.filter(meetingattendance__is_verified=True)

    @classmethod
    def get_ongoing(cls, user):
        now = timezone.now()
        return (
            cls.get_user_queryset(user)
            .filter(is_published=True, starts_at__lte=now, ends_at__gte=now)
            .first()
        )

    def get_absolute_url(self):
        return reverse("meetings_detail", args=[str(self.id)])

    def sync_discord(self, is_deleted=False):
        description = f"""**{self.get_type_display()} Meeting**
        
        View details: {settings.PUBLIC_BASE_URL}/meetings/{self.pk}
        {f'Slides: {self.presentation_url}' if self.presentation_url else ''}
        """

        try:
            if is_deleted:
                discord.delete_server_event(self.discord_event_id)
                self.discord_event_id = ""
                self.save()
            else:
                if self.is_ongoing or self.is_upcoming:
                    if not self.discord_event_id and self.is_published:
                        event = discord.create_server_event(
                            name=self.display_name,
                            scheduled_start_time=self.starts_at.isoformat(),
                            scheduled_end_time=self.ends_at.isoformat(),
                            description=description,
                            location=self.location,
                        )
                        self.discord_event_id = event["id"]
                        self.save()
                    elif self.discord_event_id and self.is_published:
                        discord.update_server_event(
                            self.discord_event_id,
                            name=self.display_name,
                            scheduled_start_time=self.starts_at.isoformat(),
                            scheduled_end_time=self.ends_at.isoformat(),
                            description=description,
                            location=self.location,
                        )
                    elif self.discord_event_id and not self.is_published:
                        discord.delete_server_event(self.discord_event_id)
                        self.discord_event_id = ""
                        self.save()
        except Exception as e:
            capture_exception(e)

    def __str__(self) -> str:
        return f"{self.display_name} - {formats.date_format(timezone.localtime(self.starts_at), 'D M j Y @ P')}"

    @classmethod
    def get_user_queryset(cls, user):
        if user.is_authenticated:
            active_enrollment = user.get_active_enrollment()
            queryset = cls.objects
            if user.is_superuser or (
                active_enrollment and active_enrollment.is_coordinator
            ):
                pass
            elif active_enrollment and active_enrollment.is_mentor:
                queryset = queryset.exclude(
                    is_published=False, type=Meeting.COORDINATOR
                )
            else:
                queryset = queryset.exclude(
                    is_published=False, type__in=(Meeting.MENTOR, Meeting.COORDINATOR)
                )
        else:
            queryset = cls.public

        return queryset

    class Meta:
        ordering = ["starts_at"]
        get_latest_by = ["starts_at"]


# post_save.connect(sync_discord, sender=Meeting)
# post_delete.connect(sync_discord_on_delete, sender=Meeting)


class MeetingAttendance(TimestampedModel):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=True)
    is_added_by_admin = models.BooleanField(
        default=False,
        help_text="Whether this attendance was added by an admin instead of by the user",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["meeting", "user"], name="unique_meeting_attendance"
            )
        ]


class MentorApplication(TimestampedModel):
    """Represents a submitted application by a student to be a Mentor for a particular semester."""

    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="mentor_applications"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="mentor_applications"
    )
    why = models.TextField(
        max_length=10000, help_text="Why do you want to be a Mentor?"
    )
    skills = models.ManyToManyField(
        ProjectTag,
        blank=True,
        related_name="mentors",
        help_text="What skills can you offer help for?",
    )
    is_accepted = models.BooleanField(
        "accepted?", null=True, default=None, help_text="Was this application accepted"
    )

    def accept(self):
        if not self.semester.is_active:
            return

        self.is_accepted = True
        self.save()

        Enrollment.objects.update_or_create(
            user=self.user_id, semester=self.semester_id, defaults={"is_mentor": True}
        )

        # TODO: figure out message
        # self.user.send_message()

    def deny(self):
        if not self.semester.is_active:
            return

        self.is_accepted = False
        self.save()

        # TODO: figure out message
        # self.user.send_message()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["semester", "user"], name="unique_mentor_application"
            )
        ]


class SmallGroup(TimestampedModel):
    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE,
        related_name="small_groups",
    )
    name = models.CharField(
        max_length=100, blank=True, help_text="Public-facing name of the Small Group"
    )
    room = models.ForeignKey(Room, on_delete=models.RESTRICT, blank=True, null=True)
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="The location the Small Group meets for Small Group meetings",
    )
    discord_category_id = models.CharField(max_length=200, blank=True)
    discord_role_id = models.CharField(max_length=200, blank=True)

    projects = models.ManyToManyField(Project, related_name="small_groups")
    mentors = models.ManyToManyField(User, related_name="mentored_small_groups")

    @property
    def display_name(self):
        return self.name or self.location or "Unnamed Small Group"

    def get_absolute_url(self):
        return reverse("small_groups_detail", args=[str(self.id)])

    def get_enrollments(self):
        return Enrollment.objects.filter(
            semester=self.semester,
            project__in=self.projects.values_list("pk", flat=True),
        )

    def get_users(self):
        return User.objects.filter(enrollments__in=self.get_enrollments())

    def has_user(self, user):
        return (
            self.projects.filter(
                enrollments__user=user, enrollments__semester=self.semester
            ).count()
            > 0
        )

    def __str__(self) -> str:
        return self.display_name

    class Meta:
        ordering = ["semester", Lower("name"), "location"]


class MeetingAttendanceCode(TimestampedModel):
    code = models.CharField(max_length=20, primary_key=True)
    meeting = models.ForeignKey(
        Meeting, on_delete=models.CASCADE, related_name="attendance_codes"
    )
    small_group = models.ForeignKey(
        SmallGroup,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="attendance_codes",
    )

    @property
    def is_valid(self):
        return self.meeting.is_ongoing

    def __str__(self) -> str:
        return self.code or "Unknown Attendance Code"

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["meeting"]),
            models.Index(fields=["meeting", "small_group"]),
        ]
        constraints = [
            # Don't allow multiple attendance codes for the same meeting and small group
            # Unfortunately, this doesn't prevent duplicate attendance codes for null small group and same meeting
            models.UniqueConstraint(
                fields=["meeting", "small_group"],
                name="unique_meeting_attendance_small_group_code",
            )
        ]


class StatusUpdate(TimestampedModel):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="status_updates"
    )
    name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional title to display on Status Update page",
    )
    opens_at = models.DateTimeField(
        help_text="The date and time the status update opens for submissions"
    )
    closes_at = models.DateTimeField(
        help_text="The date and time the status update stops accepting submissions"
    )

    @property
    def display_name(self):
        return (
            (self.name or "Status Update")
            + " "
            + timezone.localtime(self.opens_at).strftime("%x")
        )

    def __str__(self) -> str:
        return self.display_name

    class Meta:
        ordering = ("semester", "opens_at")
        get_latest_by = "opens_at"


class StatusUpdateSubmission(TimestampedModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="status_update_submissions"
    )
    status_update = models.ForeignKey(
        StatusUpdate, on_delete=models.CASCADE, related_name="submissions"
    )

    previous_week = models.TextField(max_length=10000)
    next_week = models.TextField(max_length=10000)
    blockers = models.TextField(max_length=10000)

    grade = models.DecimalField(
        max_digits=1,
        null=True,
        blank=True,
        decimal_places=1,
        help_text="The grade assigned to this submission",
    )
    grader = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="graded_status_update_submissions",
    )
    grader_comments = models.TextField(
        max_length=10000,
        blank=True,
        help_text="Optional comments from the grader to the submitter",
    )

    def __str__(self) -> str:
        return f"{self.user.display_name} submission for {self.status_update}"

    class Meta:
        ordering = ["created_at"]
