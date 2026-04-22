# Generated manually for registration invite flow

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0022_add_project_management'),
    ]

    operations = [
        migrations.CreateModel(
            name='RegistrationInvite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(db_index=True, max_length=64, unique=True, verbose_name='邀请令牌')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('expires_at', models.DateTimeField(verbose_name='过期时间')),
                ('used_at', models.DateTimeField(blank=True, null=True, verbose_name='使用时间')),
                ('created_by', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sent_registration_invites',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='创建人',
                )),
                ('registered_user', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='registration_via_invite',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='注册用户',
                )),
            ],
            options={
                'verbose_name': '注册邀请',
                'verbose_name_plural': '注册邀请',
                'ordering': ['-created_at'],
            },
        ),
    ]
