import json
from random import choice, randint, random

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

print(json.dumps(tags))

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
    projects.append(
        {
            "model": "portal.Project",
            "pk": i,
            "fields": {
                "name": f.unique.word("adjective").capitalize() + " Project",
                "owner": choice(users)["pk"],
                "is_approved": random() > 0.2,
                "summary": f.sentence(),
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


print(json.dumps(users + projects + enrollments))
