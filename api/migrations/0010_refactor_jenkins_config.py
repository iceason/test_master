"""
Step 1: Add Jenkins config fields to ExecutorMachine.
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_backfill_project_on_testcase'),
    ]

    operations = [
        migrations.AddField(
            model_name='executormachine',
            name='jenkins_url',
            field=models.URLField(blank=True, verbose_name='Jenkins 服务器地址'),
        ),
        migrations.AddField(
            model_name='executormachine',
            name='jenkins_username',
            field=models.CharField(blank=True, max_length=255, verbose_name='Jenkins 用户名'),
        ),
        migrations.AddField(
            model_name='executormachine',
            name='jenkins_token',
            field=models.CharField(blank=True, max_length=255, verbose_name='Jenkins Token'),
        ),
    ]
