# Generated by Django 4.2.1 on 2023-05-14 02:38

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0032_room_alter_semester_project_pitch_deadline_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="semester",
            name="rooms",
            field=models.ManyToManyField(related_name="semesters", to="portal.room"),
        ),
    ]
