from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        if not User.objects.filter(username="vijay").exists():
            User.objects.create_superuser(
                username="vijay",
                email="vijay@gmail.com",
                password="Admin@123"
            )
