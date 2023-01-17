# Generated by Django 4.1.4 on 2023-01-17 19:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import portal.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "email",
                    models.EmailField(
                        max_length=254,
                        unique=True,
                        verbose_name="primary email address",
                    ),
                ),
                (
                    "is_approved",
                    models.BooleanField(
                        default=False,
                        help_text="Identity is verified and can participate in RCOS",
                        verbose_name="approved?",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[("rpi", "RPI"), ("external", "External")],
                        default="external",
                        max_length=30,
                    ),
                ),
                (
                    "rcs_id",
                    models.CharField(
                        blank=True,
                        help_text="If the user is an RPI user, their RCS ID.",
                        max_length=30,
                        unique=True,
                        verbose_name="RCS ID",
                    ),
                ),
                (
                    "graduation_year",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="If the user is an RPI user, their graduation year.",
                        null=True,
                    ),
                ),
                (
                    "discord_user_id",
                    models.CharField(
                        blank=True,
                        help_text="The user's Discord account ID from the Discord API",
                        max_length=200,
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "github_username",
                    models.CharField(
                        blank=True,
                        help_text="The user's GitHub username (not user ID)",
                        max_length=200,
                        null=True,
                        unique=True,
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "ordering": ["first_name", "last_name", "email"],
            },
            managers=[
                ("objects", portal.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Meeting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="The optional title of the meeting",
                        max_length=100,
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("small_group", "Small Group"),
                            ("large_group", "Large Group"),
                            ("workshop", "Workshop"),
                            ("mentor", "Mentor"),
                            ("coordinator", "Coordinator"),
                        ],
                        max_length=100,
                    ),
                ),
                (
                    "is_published",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the meeting is visible to users",
                        verbose_name="published?",
                    ),
                ),
                (
                    "starts_at",
                    models.DateTimeField(help_text="When the meeting starts"),
                ),
                ("ends_at", models.DateTimeField(help_text="When the meeting ends")),
                (
                    "location",
                    models.CharField(
                        blank=True,
                        help_text="Where the meeting takes place either physically or virtually",
                        max_length=500,
                    ),
                ),
                (
                    "description_markdown",
                    models.TextField(
                        blank=True,
                        help_text="Optional publicly displayed description for the meeting. Supports Markdown.",
                        max_length=10000,
                    ),
                ),
                (
                    "presentation_url",
                    models.URLField(
                        blank=True,
                        help_text="The URL to the meeting's slideshow presentation if exists",
                    ),
                ),
                ("discord_event_id", models.CharField(blank=True, max_length=23)),
            ],
            options={
                "ordering": ["starts_at"],
                "get_latest_by": ["starts_at"],
            },
        ),
        migrations.CreateModel(
            name="Project",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("slug", models.SlugField()),
                (
                    "name",
                    models.CharField(
                        help_text="The project's unique name",
                        max_length=100,
                        unique=True,
                    ),
                ),
                (
                    "is_approved",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the project has been approved by Mentors/Coordinators to participate in RCOS",
                        verbose_name="approved?",
                    ),
                ),
                (
                    "summary",
                    models.CharField(
                        blank=True,
                        help_text="One-line summary of the project",
                        max_length=100,
                    ),
                ),
                (
                    "description",
                    models.TextField(
                        help_text="A description of the project", max_length=10000
                    ),
                ),
                (
                    "external_chat_url",
                    models.URLField(
                        blank=True,
                        help_text="Optional URL to an external chat that this project uses",
                    ),
                ),
                (
                    "homepage_url",
                    models.URLField(
                        blank=True,
                        help_text="Optional URL to a homepage for the project, potentially where it is publicly deployed or to documentation",
                    ),
                ),
                ("discord_role_id", models.CharField(blank=True, max_length=200)),
                (
                    "discord_text_channel_id",
                    models.CharField(blank=True, max_length=200),
                ),
                (
                    "discord_voice_channel_id",
                    models.CharField(blank=True, max_length=200),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        help_text="The user that can make edits to the project",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="owned_projects",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name"],
                "get_latest_by": "created_at",
            },
        ),
        migrations.CreateModel(
            name="ProjectTag",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=100)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Semester",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.CharField(
                        help_text="The unique ID of the semseter in RPI's format of YYYYMM where YYYY is the starting year and MM is the starting month.",
                        max_length=6,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="User-facing name of semester, e.g. Fall 2022",
                        max_length=30,
                    ),
                ),
                (
                    "is_accepting_new_projects",
                    models.BooleanField(
                        default=False,
                        help_text="Whether new projects can be proposed for this semester",
                        verbose_name="accepting new projects?",
                    ),
                ),
                (
                    "start_date",
                    models.DateField(
                        help_text="The first day of the semester according to the RPI Academic Calendar: https://info.rpi.edu/registrar/academic-calendar",
                        verbose_name="first day",
                    ),
                ),
                (
                    "end_date",
                    models.DateField(
                        help_text="The last day of the semester according to the RPI Academic Calendar: https://info.rpi.edu/registrar/academic-calendar",
                        verbose_name="last day",
                    ),
                ),
            ],
            options={
                "ordering": ["-start_date"],
            },
        ),
        migrations.CreateModel(
            name="StatusUpdate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Optional title to display on Status Update page",
                        max_length=200,
                    ),
                ),
                (
                    "opens_at",
                    models.DateTimeField(
                        help_text="The date and time the status update opens for submissions"
                    ),
                ),
                (
                    "closes_at",
                    models.DateTimeField(
                        help_text="The date and time the status update stops accepting submissions"
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_updates",
                        to="portal.semester",
                    ),
                ),
            ],
            options={
                "ordering": ("semester", "opens_at"),
                "get_latest_by": "opens_at",
            },
        ),
        migrations.CreateModel(
            name="StatusUpdateSubmission",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("previous_week", models.TextField(max_length=10000)),
                ("next_week", models.TextField(max_length=10000)),
                ("blockers", models.TextField(max_length=10000)),
                (
                    "grade",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        help_text="The grade assigned to this submission",
                        max_digits=1,
                        null=True,
                    ),
                ),
                (
                    "grader_comments",
                    models.TextField(
                        blank=True,
                        help_text="Optional comments from the grader to the submitter",
                        max_length=10000,
                    ),
                ),
                (
                    "grader",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="graded_status_update_submissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "status_update",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="submissions",
                        to="portal.statusupdate",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="status_update_submissions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="SmallGroup",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "name",
                    models.CharField(
                        blank=True,
                        help_text="Public-facing name of the Small Group",
                        max_length=100,
                    ),
                ),
                (
                    "location",
                    models.CharField(
                        help_text="The location the Small Group meets for Small Group meetings",
                        max_length=200,
                    ),
                ),
                ("discord_category_id", models.CharField(blank=True, max_length=200)),
                ("discord_role_id", models.CharField(blank=True, max_length=200)),
                (
                    "mentors",
                    models.ManyToManyField(
                        related_name="mentored_small_groups",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "projects",
                    models.ManyToManyField(
                        related_name="small_groups", to="portal.project"
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="small_groups",
                        to="portal.semester",
                    ),
                ),
            ],
            options={
                "ordering": ["semester", "name", "location"],
            },
        ),
        migrations.CreateModel(
            name="ProjectRepository",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("url", models.URLField(help_text="URL of GitHub repository")),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="repositories",
                        to="portal.project",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ProjectProposal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "url",
                    models.URLField(help_text="Link to the actual proposal document"),
                ),
                (
                    "grade",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        help_text="The grade assigned to this proposal",
                        max_digits=3,
                        null=True,
                    ),
                ),
                (
                    "grader_comments",
                    models.TextField(
                        blank=True,
                        help_text="Optional comments from the grader",
                        max_length=10000,
                    ),
                ),
                (
                    "grader",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="graded_project_proposals",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="proposals",
                        to="portal.project",
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="project_proposals",
                        to="portal.semester",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ProjectPresentation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("url", models.URLField(help_text="Link to the actual presentation")),
                (
                    "grade",
                    models.DecimalField(
                        blank=True,
                        decimal_places=1,
                        help_text="The grade assigned to this presentation",
                        max_digits=3,
                        null=True,
                    ),
                ),
                (
                    "grader_comments",
                    models.TextField(
                        blank=True,
                        help_text="Optional comments from the grader",
                        max_length=10000,
                    ),
                ),
                (
                    "grader",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="graded_project_presentations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="presentations",
                        to="portal.project",
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="project_presentations",
                        to="portal.semester",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="project",
            name="tags",
            field=models.ManyToManyField(
                blank=True, related_name="projects", to="portal.projecttag"
            ),
        ),
        migrations.CreateModel(
            name="MeetingAttendanceCode",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "code",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                (
                    "meeting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_codes",
                        to="portal.meeting",
                    ),
                ),
                (
                    "small_group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="attendance_codes",
                        to="portal.smallgroup",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="MeetingAttendance",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("is_verified", models.BooleanField(default=True)),
                (
                    "is_added_by_admin",
                    models.BooleanField(
                        default=False,
                        help_text="Whether this attendance was added by an admin instead of by the user",
                    ),
                ),
                (
                    "meeting",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="portal.meeting"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="meeting",
            name="attendances",
            field=models.ManyToManyField(
                related_name="meeting_attendances",
                through="portal.MeetingAttendance",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="meeting",
            name="host",
            field=models.ForeignKey(
                blank=True,
                help_text="Optional host for the meeting (e.g. mentor hosting a workshop",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="meeting",
            name="semester",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="meetings",
                to="portal.semester",
            ),
        ),
        migrations.CreateModel(
            name="Enrollment",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "credits",
                    models.IntegerField(
                        default=0,
                        help_text="How many course credits the user is participating in RCOS for this semester. 0 means just for experience.",
                    ),
                ),
                (
                    "is_for_pay",
                    models.BooleanField(
                        default=False,
                        help_text="Whether the user is participating in RCOS for pay instead of course credit",
                        verbose_name="for pay?",
                    ),
                ),
                (
                    "is_project_lead",
                    models.BooleanField(default=False, verbose_name="project lead?"),
                ),
                (
                    "is_coordinator",
                    models.BooleanField(default=False, verbose_name="coordinator?"),
                ),
                (
                    "is_faculty_advisor",
                    models.BooleanField(default=False, verbose_name="faculty advisor?"),
                ),
                (
                    "final_grade",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="The user's final grade for this semester (if taken for credits)",
                        max_digits=3,
                        null=True,
                    ),
                ),
                (
                    "notes_markdown",
                    models.TextField(
                        blank=True,
                        help_text="Private notes for admins about this user for this semester",
                        max_length=10000,
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="enrollments",
                        to="portal.project",
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to="portal.semester",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="enrollments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["semester"],
                "get_latest_by": ["semester"],
            },
        ),
        migrations.CreateModel(
            name="ProjectPitch",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "url",
                    models.URLField(
                        help_text="Direct link to the pitch presentation (usually a Google Slides link)",
                        verbose_name="Presentation URL",
                    ),
                ),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pitches",
                        to="portal.project",
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="project_pitches",
                        to="portal.semester",
                    ),
                ),
            ],
            options={
                "unique_together": {("semester", "project")},
            },
        ),
        migrations.AddIndex(
            model_name="project",
            index=models.Index(
                fields=["name", "summary", "description"],
                name="portal_proj_name_ae220a_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="meetingattendancecode",
            unique_together={("code", "meeting", "small_group")},
        ),
        migrations.AlterUniqueTogether(
            name="meetingattendance",
            unique_together={("meeting", "user")},
        ),
        migrations.AlterUniqueTogether(
            name="enrollment",
            unique_together={("semester", "user")},
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["is_approved"], name="portal_user_is_appr_2439f2_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["email"], name="portal_user_email_8d6b8e_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(fields=["rcs_id"], name="portal_user_rcs_id_47e388_idx"),
        ),
        migrations.AddIndex(
            model_name="user",
            index=models.Index(
                fields=["first_name", "last_name"],
                name="portal_user_first_n_13e075_idx",
            ),
        ),
    ]
