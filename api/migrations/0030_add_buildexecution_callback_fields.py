from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0029_add_buildplan_repeat_config'),
    ]

    operations = [
        migrations.AddField(
            model_name='buildexecution',
            name='callback_last_response',
            field=models.TextField(blank=True, verbose_name='回调响应摘要'),
        ),
        migrations.AddField(
            model_name='buildexecution',
            name='callback_notified',
            field=models.BooleanField(default=False, verbose_name='是否已回调'),
        ),
        migrations.AddField(
            model_name='buildexecution',
            name='callback_notified_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='回调时间'),
        ),
        migrations.AddField(
            model_name='buildexecution',
            name='callback_url',
            field=models.URLField(blank=True, verbose_name='结果回调地址'),
        ),
    ]
