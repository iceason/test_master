from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_add_dingtalk_group'),
    ]

    operations = [
        migrations.CreateModel(
            name='DingTalkTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='模板名称')),
                ('title_template', models.CharField(default='{{status_emoji}} [Test Master] {{plan_name}} - {{status_upper}}', max_length=255, verbose_name='标题模板')),
                ('body_template', models.TextField(default='## {{status_emoji}} 自动化构建通知\n\n### 基本信息\n- 构建计划：{{plan_name}}\n- 执行结果：{{status_upper}}\n- 执行时间：{{timestamp}}\n- 执行耗时：{{duration}}\n\n### 触发信息\n- 触发方式：{{trigger_type}}\n- 触发人：{{triggered_by}}\n\n### 构建详情\n- Jenkins 链接：{{jenkins_url}}\n\n---\n说明：\n- SUCCESS：所有步骤执行通过\n- FAILED：存在失败步骤，请及时排查\n- CANCELLED：构建被取消\n', verbose_name='正文模板')),
                ('is_default', models.BooleanField(default=False, verbose_name='默认模板')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('description', models.TextField(blank=True, default='', verbose_name='描述')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '钉钉模板',
                'verbose_name_plural': '钉钉模板',
                'ordering': ['-is_default', '-updated_at'],
            },
        ),
    ]
