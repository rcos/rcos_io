# Generated by Django 4.1.4 on 2022-12-31 18:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portal", "0003_project_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="slug",
            field=models.SlugField(default="default-slug"),
            preserve_default=False,
        ),
    ]