import logging
from csv import DictReader
from io import TextIOWrapper
from typing import TypedDict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render

from portal.forms import SemesterCSVUploadForm
from portal.models import Enrollment, Project, ProjectPitch, Semester, SmallGroup, User

logger = logging.getLogger(__name__)


def is_admin(user):
    return user.is_superuser


SubmittyCSVRow = TypedDict(
    "SubmittyCSVRow",
    {
        "First Name": str,
        "Last Name": str,
        "User ID": str,
        "Email": str,
        "Secondary Email": str,
        "Registration Section": str,
        "Rotation Section": int,
        "Group": str,
    },
)

# e.g. "Frank,Matranga,merchb,00001_nib2,BidOS,4,9"
SubmittyWithTeamsCSVRow = TypedDict(
    "SubmittyWithTeamsCSVRow",
    {
        "Given Name": str,
        "Family Name": str,
        "User ID": str,  # RCS ID
        "Team ID": str,  # {id}_{project lead rcs id}
        "Team Name": str,  # project name
        "Team Registration Section": str,
        "Team Rotating Section": str,
    },
)

GoogleFormProjectPitchRow = TypedDict(
    "GoogleFormProjectPitchRow",
    {
        "Timestamp": str,
        "Email Address": str,
        "First Name": str,
        "Last Name": str,
        "RPI Email (@rpi.edu)": str,
        "What is the name of the project?": str,
        "What is your project about?": int,
        "Has this project been worked on before in RCOS?": str,
        "Pitch Slide": str,
    },
)

AttendanceExportRow = TypedDict("AttendanceExportRow", {
    "user id": str,
    "given name": str,
    "family name": str,
    "grade1": float,
    "totalgrade": float
})

@login_required
@user_passes_test(is_admin)
def import_submitty_enrollments(request):
    if request.method == "POST":
        form = SemesterCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["csv"]
            semester = Semester.objects.get(pk=request.POST["semester"])

            rows = TextIOWrapper(file, encoding="utf-8", newline="")
            for row in DictReader(rows):
                row: SubmittyCSVRow

                if not row["Email"]:
                    logger.warning("Skipping %s", row)
                    continue

                try:
                    rcs_id = row["Email"].removesuffix("@rpi.edu")
                    # Find or create user
                    try:
                        user = User.objects.get(
                            Q(rcs_id=rcs_id) | Q(email=row["Email"])
                        )
                    except User.DoesNotExist:
                        user = User(email=row["Email"])

                    if not user.first_name:
                        user.first_name = row["First Name"]
                    if not user.last_name:
                        user.last_name = row["Last Name"]

                    user.save()
                    try:
                        credits = int(row["Registration Section"])
                    except ValueError:
                        credits = 0

                    # Upsert enrollment
                    enrollment, is_new = Enrollment.objects.update_or_create(
                        semester=semester, user=user, defaults={"credits": credits}
                    )

                    logger.info(
                        "Created" if is_new else "Updated", "enrollment", enrollment
                    )
                except:
                    pass
    else:
        form = SemesterCSVUploadForm()

    return render(
        request,
        "portal/admin/import/import.html",
        {
            "title": "Import Student Enrollments from Submitty",
            "source": "Submitty",
            "form": form,
            "expected_columns": SubmittyCSVRow.__required_keys__,
        },
    )


@login_required
@user_passes_test(is_admin)
def import_submitty_teams(request):
    if request.method == "POST":
        form = SemesterCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["csv"]
            semester = Semester.objects.get(pk=request.POST["semester"])

            rows = TextIOWrapper(file, encoding="utf-8", newline="")
            for row in DictReader(rows):
                row: SubmittyWithTeamsCSVRow
                try:
                    rcs_id = row["User ID"]
                    # Find or create user
                    try:
                        user = User.objects.get(rcs_id=rcs_id)
                    except User.DoesNotExist:
                        user = User(email=rcs_id + "@rpi.edu")

                    if not user.first_name:
                        user.first_name = row["Given Name"]
                    if not user.last_name:
                        user.last_name = row["Family Name"]

                    user.save()
                    try:
                        credits = int(row["Team Registration Section"])
                        if not (0 <= credits <= 4):
                            credits = 0
                    except ValueError:
                        logger.warning(
                            f"Failed to parse credits: '{row['Team Registration Section']}' defaulting to 0"
                        )
                        credits = 0

                    defaults = {"credits": credits}

                    # Upsert project
                    if row["Team Name"].strip():
                        owner_rcs_id = row["Team ID"].split("_")[1]
                        owner = User.objects.filter(rcs_id=owner_rcs_id).first()
                        project, is_new = Project.objects.update_or_create(
                            name__iexact=row["Team Name"],
                            defaults={
                                "owner": owner,
                                "name": row["Team Name"],
                                "is_approved": True,
                            },
                        )
                        defaults["project"] = project
                        defaults["is_project_lead"] = rcs_id == owner_rcs_id

                        # Upsert small group
                        small_group, is_new = SmallGroup.objects.get_or_create(
                            semester=semester,
                            name=f"Small Group {row['Team Rotating Section']}",
                        )
                        small_group.projects.add(project)

                    # Upsert enrollment
                    enrollment, is_new = Enrollment.objects.update_or_create(
                        semester=semester, user=user, defaults=defaults
                    )

                    logger.info(
                        "Created" if is_new else "Updated", "enrollment", enrollment
                    )
                except:
                    pass
            messages.success(request, "Successfully imported projects and teams!")
    else:
        form = SemesterCSVUploadForm()

    return render(
        request,
        "portal/admin/import/import.html",
        {
            "title": "Import Teams from Submitty",
            "source": "Submitty",
            "form": form,
            "expected_columns": SubmittyWithTeamsCSVRow.__required_keys__,
        },
    )


@login_required
@user_passes_test(is_admin)
def import_google_form_projects(request):
    if request.method == "POST":
        form = SemesterCSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["csv"]
            semester = Semester.objects.get(pk=request.POST["semester"])

            rows = TextIOWrapper(file, encoding="utf-8", newline="")
            for row in DictReader(rows):
                row: GoogleFormProjectPitchRow

                try:
                    rcs_id = row["RPI Email (@rpi.edu)"].removesuffix("@rpi.edu")
                    # Find or create user
                    try:
                        user = User.objects.get(
                            Q(rcs_id=rcs_id) | Q(email=row["RPI Email (@rpi.edu)"])
                        )
                    except User.DoesNotExist:
                        user = User(email=row["RPI Email (@rpi.edu)"])

                    user.save()

                    project, is_created = Project.objects.update_or_create(
                        name=row["What is the name of the project?"],
                        defaults={
                            "description": row["What is your project about?"],
                            "is_approved": True,
                            "owner": user,
                        },
                    )

                    enrollment, is_created = Enrollment.objects.update_or_create(
                        user=user,
                        semester=semester,
                        defaults={"project": project, "is_project_lead": True},
                    )

                    pitch, is_created = ProjectPitch.objects.update_or_create(
                        project=project,
                        semester=semester,
                        defaults={"url": row["Pitch Slide"]},
                    )

                    logger.info(
                        "Imported row %s", row["What is the name of the project?"]
                    )
                except Exception as e:
                    logger.error("Failed to import row %s: %s", row, e)
    else:
        form = SemesterCSVUploadForm()

    return render(
        request,
        "portal/admin/import/import.html",
        {
            "title": "Import Projects from Google Forms",
            "source": "Google Forms",
            "form": form,
            "expected_columns": GoogleFormProjectPitchRow.__required_keys__,
        },
    )