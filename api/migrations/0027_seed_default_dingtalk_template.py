from django.db import migrations


def seed_default_template(apps, schema_editor):
    DingTalkTemplate = apps.get_model('api', 'DingTalkTemplate')
    DingTalkTemplate.objects.get_or_create(
        name='默认中文模板',
        defaults={
            'title_template': '{{status_emoji}} [Test Master] {{plan_name}} - {{status_upper}}',
            'body_template': (
                "## {{status_emoji}} 自动化构建通知\n\n"
                "### 基本信息\n"
                "- 构建计划：{{plan_name}}\n"
                "- 执行结果：{{status_upper}}\n"
                "- 执行时间：{{timestamp}}\n"
                "- 执行耗时：{{duration}}\n\n"
                "### 触发信息\n"
                "- 触发方式：{{trigger_type}}\n"
                "- 触发人：{{triggered_by}}\n\n"
                "### 构建详情\n"
                "- Jenkins 链接：{{jenkins_url}}\n\n"
                "---\n"
                "说明：\n"
                "- SUCCESS：所有步骤执行通过\n"
                "- FAILED：存在失败步骤，请及时排查\n"
                "- CANCELLED：构建被取消\n"
            ),
            'is_default': True,
            'is_active': True,
            'description': '系统初始化模板',
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_migrate_notification_webhook_to_dingtalk'),
    ]

    operations = [
        migrations.RunPython(seed_default_template, migrations.RunPython.noop),
    ]
