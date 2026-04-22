from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_refresh_default_dingtalk_template_content'),
    ]

    operations = [
        migrations.AddField(
            model_name='buildplan',
            name='repeat_failure_policy',
            field=models.CharField(
                choices=[('continue_all', '继续全部轮次'), ('stop_on_first_fail', '首次失败即停止')],
                default='continue_all',
                max_length=30,
                verbose_name='重复执行失败策略',
            ),
        ),
        migrations.AddField(
            model_name='buildplan',
            name='repeat_run_times',
            field=models.PositiveIntegerField(
                default=1,
                help_text='点击一次立即构建时，自动触发的轮次（1~20）',
                validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(20)],
                verbose_name='重复执行次数',
            ),
        ),
    ]
