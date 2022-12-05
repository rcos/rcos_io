from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Semester(TimestampedModel):
    id = models.CharField(max_length=len("202201"), primary_key=True)
    name = models.CharField(
        max_length=30, help_text="User-facing name of semester, e.g. Fall 2022"
    )
    is_accepting_new_projects = models.BooleanField(
        default=False,
        help_text="Whether new projects can be proposed for this semester",
    )
    start_date = models.DateField("start of semester")
    end_date = models.DateField("end of semester")


class User(TimestampedModel):
    RPI = "rpi"
    EXTERNAL = "external"
    ROLE_CHOICES = ((RPI, "RPI"), (EXTERNAL, "External"))

    is_approved = models.BooleanField(default=False)
    role = models.CharField(choices=ROLE_CHOICES, max_length=30)

    # Profile
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    email = models.EmailField(unique=True)

    # Set for RPI users only
    rcs_id = models.CharField(null=True, max_length=30)
    graduation_year = models.PositiveIntegerField(null=True)

    # Account integrations
    discord_user_id = models.CharField(null=True, max_length=200)
    github_username = models.CharField(null=True, max_length=200)

    class Meta:
        ordering = ["rcs_id", "first_name", "last_name"]


class Project(TimestampedModel):
    name = models.CharField(max_length=100, unique=True)
    owner = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL, related_name="owned_projects"
    )
    is_approved = models.BooleanField(default=False)
    tagline = models.CharField(max_length=200)
    description_markdown = models.TextField(max_length=10000)
    enrollments = models.ManyToManyField(User, through="Enrollment")
    is_seeking_members = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        get_latest_by = "created_at"


class Enrollment(TimestampedModel):
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="enrollments")
    project = models.ForeignKey(Project, null=True, on_delete=models.SET_NULL)
    credits = models.IntegerField(default=0)
    is_for_pay = models.BooleanField(default=False)
    is_project_lead = models.BooleanField(default=False)
    is_faculty_advisor = models.BooleanField(default=False)
    is_faculty_advisor = models.BooleanField(default=False)

    class Meta:
        ordering = ["semester"]
        get_latest_by = ["semester"]
