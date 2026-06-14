from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create admin user only'

    def handle(self, *args, **kwargs):
        from core.models import User

        self.stdout.write('🌸 Creating Admin User...')

        admin, created = User.objects.get_or_create(
            email='vrajvadhudevidasi@gmail.com',
            defaults={
                'name': 'Vrajvadhu Devi Dasi',
                'role': 'admin',
                'city': 'Solapur',
                'is_staff': True,
                'is_superuser': True,
            }
        )

        admin.set_password('igfadmin123')
        admin.save()

        self.stdout.write(
            self.style.SUCCESS(
                '✅ Admin created successfully!\n'
                'Email: vrajvadhudevidasi@gmail.com\n'
                'Password: igfadmin123'
            )
        )