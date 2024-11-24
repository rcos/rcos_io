import json
from random import choice, randint, random
from django.utils.text import slugify

from faker import Faker

f = Faker()

tags_raw = [
    "javascript",
    "typescript",
    "python",
    "html",
    "css",
    "c",
    "c++",
    "rust",
    "c#",
    "php",
    "swift",
    "r",
    "golang",
    "ruby",
    "sql",
    "kotlin",
    "hardware",
]

tags = [
    {
        "model": "portal.ProjectTag",
        "pk": index,
        "fields": {
            "name": tag,
            "updated_at": "2022-12-29T02:30:00+0000",
            "created_at": "2022-12-29T02:30:00+0000",
        },
    }
    for index, tag in enumerate(tags_raw)
]

semester_ids = ["202201", "202208", "202301"]
semesters = [
    {
        "model": "portal.Semester",
        "pk": semester_id,
        "fields": {
            "name": semester_id,
            "start_date": "2023-12-29",
            "end_date": "2024-12-29",
            "updated_at": "2022-12-29",
            "created_at": "2022-12-29",
        },
    }
    for semester_id in semester_ids
]

users = []
for i in range(2, 50):
    users.append(
        {
            "model": "portal.User",
            "pk": i,
            "fields": {
                "email": f"student{i}@rpi.edu",
                "first_name": f.first_name(),
                "last_name": f.last_name(),
                "is_approved": random() > 0.1,
                "role": "rpi",
                "rcs_id": f"student{i}",
                "graduation_year": randint(2022, 2025),
                "updated_at": "2022-12-29T02:30:00+0000",
                "created_at": "2022-12-29T02:30:00+0000",
            },
        }
    )

# print(json.dumps(users))

projects = []
for i in range(30):
    name = f.unique.word("adjective").capitalize() + " Project"
    projects.append(
        {
            "model": "portal.Project",
            "pk": i,
            "fields": {
                "name": name,
                "slug": slugify(name),
                "owner": choice(users)["pk"],
                "is_approved": random() > 0.2,
                "description": f.sentence(),
                "updated_at": "2022-12-29T02:30:00+0000",
                "created_at": "2022-12-29T02:30:00+0000",
            },
        }
    )

enrollments = []
pk = 1
for user in users:
    enrollments.append(
        {
            "model": "portal.Enrollment",
            "pk": pk,
            "fields": {
                "semester": "202301",
                "user": user["pk"],
                "project": choice(projects)["pk"],
                "credits": randint(0, 4),
                "is_project_lead": random() > 0.7,
                "updated_at": "2022-12-29T02:30:00+0000",
                "created_at": "2022-12-29T02:30:00+0000",
            },
        }
    )
    pk += 1
    enrollments.append(
        {
            "model": "portal.Enrollment",
            "pk": pk,
            "fields": {
                "semester": "202208",
                "user": user["pk"],
                "project": choice(projects)["pk"],
                "credits": randint(0, 4),
                "is_project_lead": random() > 0.7,
                "updated_at": "2022-12-29T02:30:00+0000",
                "created_at": "2022-12-29T02:30:00+0000",
            },
        }
    )
    pk += 1
    enrollments.append(
        {
            "model": "portal.Enrollment",
            "pk": pk,
            "fields": {
                "semester": "202201",
                "user": user["pk"],
                "project": choice(projects)["pk"],
                "credits": randint(0, 4),
                "is_project_lead": random() > 0.7,
                "updated_at": "2022-12-29T02:30:00+0000",
                "created_at": "2022-12-29T02:30:00+0000",
            },
        }
    )
    pk += 1


print(json.dumps([*semesters, *tags, *users, *projects, *enrollments], indent=4))
