from django.db import migrations


def refresh_default_template(apps, schema_editor):
    DingTalkTemplate = apps.get_model('api', 'DingTalkTemplate')
    tpl = DingTalkTemplate.objects.filter(name='默认中文模板').first()
    if not tpl:
        return

    tpl.title_template = '{{status_emoji}} [Test Master] {{plan_name}} - {{status_upper}}'
    tpl.body_template = (
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
    )
    tpl.save(update_fields=['title_template', 'body_template', 'updated_at'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0027_seed_default_dingtalk_template'),
    ]

    operations = [
        migrations.RunPython(refresh_default_template, migrations.RunPython.noop),
    ]
