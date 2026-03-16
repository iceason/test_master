from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create default dev user 'admin' with password '12345678' if not exists"

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_user('admin', password='12345678')
            self.stdout.write(self.style.SUCCESS("Created user 'admin'"))
        else:
            self.stdout.write(self.style.WARNING("User 'admin' already exists"))
