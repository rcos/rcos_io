from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Semester(TimestampedModel):
    id = models.CharField(
        max_length=len("202201"),
        primary_key=True,
        help_text="The unique ID of the semseter in RPI's format of YYYYMM where YYYY is the starting year and MM is the starting month.",
    )
    name = models.CharField(
        max_length=30, help_text="User-facing name of semester, e.g. Fall 2022"
    )
    is_accepting_new_projects = models.BooleanField(
        "accepting new projects?",
        default=False,
        help_text="Whether new projects can be proposed for this semester",
    )
    start_date = models.DateField(
        "first day",
        help_text="The first day of the semester according to the RPI Academic Calendar: https://info.rpi.edu/registrar/academic-calendar",
    )
    end_date = models.DateField(
        "last day",
        help_text="The last day of the semester according to the RPI Academic Calendar: https://info.rpi.edu/registrar/academic-calendar",
    )

    @property
    def enrollment_count(self):
        return self.enrollments.count()

    @property
    def project_count(self):
        return self.enrollments.distinct("project").order_by().count()

    def __str__(self) -> str:
        return self.name


class User(TimestampedModel):
    RPI = "rpi"
    EXTERNAL = "external"
    ROLE_CHOICES = ((RPI, "RPI"), (EXTERNAL, "External"))

    is_approved = models.BooleanField("approved?", default=False)
    role = models.CharField(choices=ROLE_CHOICES, max_length=30)

    # Profile
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(
        unique=True,
        help_text="The user's primary email, used for logging in and sending communications. Can change.",
    )

    # Set for RPI users only
    rcs_id = models.CharField(
        blank=True,
        max_length=30,
        help_text="If the user is an RPI user, their RCS ID.",
        verbose_name="RCS ID",
    )
    graduation_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="If the user is an RPI user, their graduation year.",
    )

    # Account integrations
    discord_user_id = models.CharField(
        blank=True,
        max_length=200,
        help_text="The user's Discord account ID from the Discord API",
    )
    github_username = models.CharField(
        blank=True, max_length=200, help_text="The user's GitHub username (not user ID)"
    )

    @property
    def full_name(self):
        return (self.first_name + " " + self.last_name).strip()

    @property
    def is_setup(self):
        return self.first_name and self.last_name and self.github_username and self.discord_user_id

    def __str__(self) -> str:
        return self.email

    class Meta:
        ordering = ["rcs_id", "first_name", "last_name"]


class Project(TimestampedModel):
    name = models.CharField(
        max_length=100, unique=True, help_text="The project's unique name"
    )
    owner = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="owned_projects",
        help_text="The user that can make edits to the project",
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Whether the project has been approved by Mentors/Coordinators to participate in RCOS",
    )
    tagline = models.CharField(
        max_length=200, help_text="A one-line description of the project"
    )
    description_markdown = models.TextField(
        max_length=10000,
        help_text="A long description of the project. Supports Markdown.",
    )
    is_seeking_members = models.BooleanField(
        default=False,
        help_text="Whether the project is actively looking for new members to join",
    )

    # Relationships
    # enrollments = models.ManyToManyField(User, through="Enrollment")

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]
        get_latest_by = "created_at"


class Enrollment(TimestampedModel):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="enrollments")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    project = models.ForeignKey(
        Project, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="enrollments"
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
    is_faculty_advisor = models.BooleanField("faculty advisor?", default=False)

    def __str__(self) -> str:
        return f"{self.semester.name} - {self.user} - {self.project or 'No project'}"

    class Meta:
        unique_together = ("semester", "user")
        ordering = ["semester"]
        get_latest_by = ["semester"]

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
        (COORDINATOR, "Coordinator")
    )

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="meetings")
    name = models.CharField(max_length=100, blank=True, help_text="The optional title of the meeting")
    host = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, help_text="Optional host for the meeting (e.g. mentor hosting a workshop")
    type = models.CharField(choices=TYPE_CHOICES, max_length=100)
    is_published = models.BooleanField("published?", default=False, help_text="Whether the meeting is visible to users")
    starts_at = models.DateTimeField(help_text="When the meeting starts")
    ends_at = models.DateTimeField(help_text="When the meeting ends")
    location = models.CharField(max_length=500, blank=True, help_text="Where the meeting takes place either physically or virtually")
    description_markdown = models.TextField(max_length=10000, blank=True, help_text="Optional publicly displayed description for the meeting. Supports Markdown.")

    # Relationships
    attendances = models.ManyToManyField(User, through="MeetingAttendance", related_name="meeting_attendances")

    def __str__(self) -> str:
        return f"{self.name} - {self.get_type_display()} - {self.starts_at.strftime('%a %b %-d %Y @ %-I:%M %p')}" 

    class Meta:
        ordering = ["starts_at"]

class MeetingAttendance(TimestampedModel):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_added_by_admin = models.BooleanField(default=False, help_text="Whether this attendance was added by an admin instead of by the user")
