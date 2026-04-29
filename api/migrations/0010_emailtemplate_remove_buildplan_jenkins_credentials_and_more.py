# Legacy branch migration kept for graph compatibility only.
# The actual schema changes in this branch have been superseded by
# the 0010_refactor_jenkins_config -> ... -> 003x mainline migrations.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_backfill_project_on_testcase'),
    ]

    operations = []
