from csv import DictReader
from io import TextIOWrapper
from typing import TypedDict

from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render

from portal.forms import UploadSubmittyDataForm
from portal.models import Enrollment, Semester, User


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


@login_required
@user_passes_test(is_admin)
def import_submitty_data(request):
    if request.method == "POST":
        form = UploadSubmittyDataForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES["submitty_csv"]
            semester = Semester.objects.get(pk=request.POST["semester"])

            rows = TextIOWrapper(file, encoding="utf-8", newline="")
            for row in DictReader(rows):
                row: SubmittyCSVRow

                if not row["Email"]:
                    print("Skipping", row)
                    continue

                rcs_id = row["Email"].removesuffix("@rpi.edu")
                # Find or create user
                try:
                    user = User.objects.get(Q(rcs_id=rcs_id) | Q(email=row["Email"]))
                    print("Found", user)
                except User.DoesNotExist:
                    user = User(email=row["Email"])
                    print("Created", user)

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

                print("Created" if is_new else "Updated", "enrollment", enrollment)
    else:
        form = UploadSubmittyDataForm()

    return render(
        request,
        "portal/admin/import.html",
        {"form": form, "expected_columns": SubmittyCSVRow.__required_keys__},
    )
