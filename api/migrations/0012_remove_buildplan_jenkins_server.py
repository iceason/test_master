"""
Step 3: Remove deprecated Jenkins config fields from BuildPlan.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_migrate_jenkins_to_executor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='buildplan',
            name='jenkins_server_url',
        ),
        migrations.RemoveField(
            model_name='buildplan',
            name='jenkins_credentials',
        ),
    ]
