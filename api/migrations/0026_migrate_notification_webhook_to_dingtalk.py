from django.db import migrations


def forward_migrate(apps, schema_editor):
    BuildPlan = apps.get_model('api', 'BuildPlan')
    DingTalkGroup = apps.get_model('api', 'DingTalkGroup')

    placeholder_secret = 'MIGRATION_REQUIRED_SET_SECRET'

    for plan in BuildPlan.objects.all():
        config = dict(plan.notification_config or {})
        dingtalk_cfg = dict(config.get('dingtalk') or {})
        webhook_cfg = dict(config.get('webhook') or {})

        if dingtalk_cfg:
            # Keep existing dingtalk config if already present.
            continue

        if webhook_cfg.get('enabled') and webhook_cfg.get('type') == 'dingtalk' and webhook_cfg.get('url'):
            url = webhook_cfg.get('url')
            group, _ = DingTalkGroup.objects.get_or_create(
                webhook_url=url,
                defaults={
                    'name': f'迁移群组-{plan.id}',
                    'secret': placeholder_secret,
                    'is_active': False,
                    'description': '由历史 webhook 配置迁移，请补充真实 secret 后启用。',
                },
            )
            config['dingtalk'] = {
                'enabled': True,
                'group_ids': [group.id],
                'template_id': None,
            }
            plan.notification_config = config
            plan.save(update_fields=['notification_config'])


def backward_migrate(apps, schema_editor):
    BuildPlan = apps.get_model('api', 'BuildPlan')
    for plan in BuildPlan.objects.all():
        config = dict(plan.notification_config or {})
        if 'dingtalk' in config:
            config.pop('dingtalk', None)
            plan.notification_config = config
            plan.save(update_fields=['notification_config'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0025_add_dingtalk_template'),
    ]

    operations = [
        migrations.RunPython(forward_migrate, backward_migrate),
    ]
