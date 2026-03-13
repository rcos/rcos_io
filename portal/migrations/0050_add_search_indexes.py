from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("portal", "0049_remove_shortlink_portal_shor_user_id_8fd83e_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="search_vector",
            field=SearchVectorField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name="project",
            name="search_vector",
            field=SearchVectorField(null=True, editable=False),
        ),
        migrations.AddIndex(
            model_name="user",
            index=GinIndex(fields=["search_vector"], name="user_search_gin"),
        ),
        migrations.AddIndex(
            model_name="project",
            index=GinIndex(fields=["search_vector"], name="project_search_gin"),
        ),
        migrations.RunSQL(
            """
            UPDATE portal_user
            SET search_vector = to_tsvector('english',
                coalesce(first_name, '') || ' ' ||
                coalesce(last_name, '') || ' ' ||
                coalesce(rcs_id, '') || ' ' ||
                coalesce(email, '')
            );
            """,
            migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            """
            UPDATE portal_project
            SET search_vector = to_tsvector('english',
                coalesce(name, '') || ' ' ||
                coalesce(description, '')
            );
            """,
            migrations.RunSQL.noop,
        ),
    ]
