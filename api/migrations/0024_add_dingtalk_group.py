from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_registration_invite'),
    ]

    operations = [
        migrations.CreateModel(
            name='DingTalkGroup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='群组名称')),
                ('webhook_url', models.URLField(verbose_name='Webhook 地址')),
                ('secret', models.CharField(max_length=255, verbose_name='签名密钥')),
                ('is_active', models.BooleanField(default=True, verbose_name='是否启用')),
                ('description', models.TextField(blank=True, default='', verbose_name='描述')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '钉钉群组',
                'verbose_name_plural': '钉钉群组',
                'ordering': ['name'],
            },
        ),
    ]
