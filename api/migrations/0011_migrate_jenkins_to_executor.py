"""
Step 2: Migrate Jenkins config from BuildPlan to ExecutorMachine.
For each BuildPlan that has jenkins_server_url configured and an associated
executor_machine, copy the Jenkins config to the ExecutorMachine (if not
already set).
"""
from django.db import migrations


def migrate_jenkins_config(apps, schema_editor):
    BuildPlan = apps.get_model('api', 'BuildPlan')
    for plan in BuildPlan.objects.exclude(jenkins_server_url='').filter(
        executor_machine__isnull=False
    ).select_related('executor_machine'):
        machine = plan.executor_machine
        if not machine.jenkins_url:
            machine.jenkins_url = plan.jenkins_server_url
            creds = plan.jenkins_credentials or {}
            machine.jenkins_username = creds.get('username', '')
            machine.jenkins_token = creds.get('token', '')
            machine.save(update_fields=[
                'jenkins_url', 'jenkins_username', 'jenkins_token',
            ])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_refactor_jenkins_config'),
    ]

    operations = [
        migrations.RunPython(migrate_jenkins_config, migrations.RunPython.noop),
    ]
