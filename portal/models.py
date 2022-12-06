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
    def display_name(self):
        chunks = []

        if self.first_name:
            chunks.append(self.first_name)
        if self.last_name:
            chunks.append(self.last_name[0])

        if self.role == User.RPI:
            if self.graduation_year:
                chunks.append(f"'{str(self.graduation_year)[2:]}")
            if self.rcs_id:
                chunks.append(f"({self.rcs_id})")

        if len(chunks) == 0:
            chunks.append(self.email)

        return " ".join(chunks).strip()

    @property
    def is_setup(self):
        return (
            self.first_name
            and self.last_name
            and self.github_username
            and self.discord_user_id
        )

    def __str__(self) -> str:
        return self.display_name

    class Meta:
        ordering = ["rcs_id", "first_name", "last_name"]


class ProjectTag(TimestampedModel):
    name = models.CharField(max_length=100)


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
        "approved?",
        default=False,
        help_text="Whether the project has been approved by Mentors/Coordinators to participate in RCOS",
    )
    summary = models.CharField(
        max_length=200, help_text="A one-line summary of the project"
    )
    description_markdown = models.TextField(
        max_length=10000,
        help_text="A long description of the project. Supports Markdown.",
    )
    is_seeking_members = models.BooleanField(
        "seeking members?",
        default=False,
        help_text="Whether the project is actively looking for new members to join",
    )

    external_chat_url = models.URLField(
        blank=True, help_text="Optional URL to an external chat that this project uses"
    )

    homepage_url = models.URLField(
        blank=True,
        help_text="Optional URL to a homepage for the project, potentially where it is deloyed",
    )

    tags = models.ManyToManyField(ProjectTag, related_name="projects")

    discord_role_id = models.CharField(max_length=200, blank=True)

    discord_text_id = models.CharField(max_length=200, blank=True)

    discord_voice_id = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return self.name

    class Meta:
        ordering = ["name"]
        get_latest_by = "created_at"


class ProjectRepository(TimestampedModel):
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="repositories"
    )
    repository_url = models.URLField(help_text="URL of GitHub repository")


class ProjectProposal(TimestampedModel):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="project_proposals"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="proposals"
    )
    proposal_url = models.URLField(help_text="Link to the actual proposal document")

    grade = models.DecimalField(
        max_digits=3,
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


class ProjectPresentation(TimestampedModel):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="project_presentations"
    )
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="presentations"
    )
    presentation_url = models.URLField(help_text="Link to the actual presentation")

    grade = models.DecimalField(
        max_digits=3,
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
    is_faculty_advisor = models.BooleanField("faculty advisor?", default=False)

    final_grade = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        help_text="The user's final grade for this semester (if taken for credits)",
        null=True,
        blank=True,
    )

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
        (COORDINATOR, "Coordinator"),
    )

    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="meetings"
    )
    name = models.CharField(
        max_length=100, blank=True, help_text="The optional title of the meeting"
    )
    host = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Optional host for the meeting (e.g. mentor hosting a workshop",
    )
    type = models.CharField(choices=TYPE_CHOICES, max_length=100)
    is_published = models.BooleanField(
        "published?", default=False, help_text="Whether the meeting is visible to users"
    )
    starts_at = models.DateTimeField(help_text="When the meeting starts")
    ends_at = models.DateTimeField(help_text="When the meeting ends")
    location = models.CharField(
        max_length=500,
        blank=True,
        help_text="Where the meeting takes place either physically or virtually",
    )
    description_markdown = models.TextField(
        max_length=10000,
        blank=True,
        help_text="Optional publicly displayed description for the meeting. Supports Markdown.",
    )

    # Relationships
    attendances = models.ManyToManyField(
        User, through="MeetingAttendance", related_name="meeting_attendances"
    )

    def __str__(self) -> str:
        return f"{self.name} - {self.get_type_display()} - {self.starts_at.strftime('%a %b %-d %Y @ %-I:%M %p')}"

    class Meta:
        ordering = ["starts_at"]


class MeetingAttendance(TimestampedModel):
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_added_by_admin = models.BooleanField(
        default=False,
        help_text="Whether this attendance was added by an admin instead of by the user",
    )


class SmallGroup(TimestampedModel):
    semester = models.ForeignKey(
        Semester, on_delete=models.CASCADE, related_name="small_groups"
    )
    name = models.CharField(
        max_length=100, blank=True, help_text="Public-facing name of the Small Group"
    )
    location = models.CharField(
        max_length=200,
        help_text="The location the Small Group meets for Small Group meetings",
    )
    discord_category_id = models.CharField(max_length=200, blank=True)
    discord_role_id = models.CharField(max_length=200, blank=True)

    projects = models.ManyToManyField(Project, related_name="small_groups")
    mentors = models.ManyToManyField(User, related_name="mentored_small_groups")

    @property
    def display_name(self):
        return self.name or self.location or "Unnamed Small Group"

    def __str__(self) -> str:
        return self.display_name

    class Meta:
        ordering = ["semester", "name", "location"]


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
        return (self.name or "Status Update") + " " + self.opens_at.strftime("%x")

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
