from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0049_remove_shortlink_portal_shor_user_id_8fd83e_idx_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="user",
            index=GinIndex(
                SearchVector("first_name", "last_name", "rcs_id", "email"),
                name="user_search_gin",
            ),
        ),
        migrations.AddIndex(
            model_name="project",
            index=GinIndex(
                SearchVector("name", "description"),
                name="project_search_gin",
            ),
        ),
    ]
