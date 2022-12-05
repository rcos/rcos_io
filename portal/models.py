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
        default=False,
        help_text="Whether new projects can be proposed for this semester",
    )
    start_date = models.DateField(
        "start of semester",
        help_text="The first day of the semester according to the RPI Academic Calendar: https://info.rpi.edu/registrar/academic-calendar",
    )
    end_date = models.DateField(
        "end of semester",
        help_text="The last day of the semester according to the RPI Academic Calendar: https://info.rpi.edu/registrar/academic-calendar",
    )


class User(TimestampedModel):
    RPI = "rpi"
    EXTERNAL = "external"
    ROLE_CHOICES = ((RPI, "RPI"), (EXTERNAL, "External"))

    is_approved = models.BooleanField(default=False)
    role = models.CharField(choices=ROLE_CHOICES, max_length=30)

    # Profile
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    email = models.EmailField(
        unique=True,
        help_text="The user's primary email, used for logging in and sending communications. Can change.",
    )

    # Set for RPI users only
    rcs_id = models.CharField(
        null=True, max_length=30, help_text="If the user is an RPI user, their RCS ID."
    )
    graduation_year = models.PositiveIntegerField(
        null=True, help_text="If the user is an RPI user, their graduation year."
    )

    # Account integrations
    discord_user_id = models.CharField(
        null=True,
        max_length=200,
        help_text="The user's Discord account ID from the Discord API",
    )
    github_username = models.CharField(
        null=True, max_length=200, help_text="The user's GitHub username (not user ID)"
    )

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
    enrollments = models.ManyToManyField(User, through="Enrollment")

    class Meta:
        ordering = ["name"]
        get_latest_by = "created_at"


class Enrollment(TimestampedModel):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL)
    credits = models.IntegerField(
        default=0,
        help_text="How many course credits the user is participating in RCOS for this semester. 0 means just for experience.",
    )
    is_for_pay = models.BooleanField(
        default=False,
        help_text="Whether the user is participating in RCOS for pay instead of course credit",
    )
    is_project_lead = models.BooleanField(default=False)
    is_faculty_advisor = models.BooleanField(default=False)
    is_faculty_advisor = models.BooleanField(default=False)

    class Meta:
        ordering = ["semester"]
        get_latest_by = ["semester"]
