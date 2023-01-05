# Generated by Django 4.1.4 on 2023-01-05 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0003_meeting_discord_event_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="homepage_url",
            field=models.URLField(
                blank=True,
                help_text="Optional URL to a homepage for the project, potentially where it is publicly deployed or to documentation",
            ),
        ),
    ]