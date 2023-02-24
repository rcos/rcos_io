# Generated by Django 4.1.4 on 2023-02-08 19:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "portal",
            "0029_remove_meetingattendancecode_unique_meeting_attendance_small_group_code_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="meetingattendancecode",
            name="small_group",
            field=models.ForeignKey(
                blank=True,
                default="",
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attendance_codes",
                to="portal.smallgroup",
            ),
            preserve_default=False,
        ),
    ]
