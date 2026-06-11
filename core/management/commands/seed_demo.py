"""
Management command: python manage.py seed_demo

Creates demo admin, mentor, and mentee accounts with sample sadhana data.
Run once after initial migrations.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
import random


class Command(BaseCommand):
    help = 'Seed the database with demo data for IGF'

    def handle(self, *args, **kwargs):
        from core.models import User, SadhanaEntry, Announcement, Lecture

        self.stdout.write('🌸 Seeding IGF demo data...')

        # ── Admin ──────────────────────────────────
        admin, _ = User.objects.get_or_create(
            email='admin@igf.org',
            defaults={
                'name': 'Radha Dasi (Admin)',
                'role': 'admin',
                'city': 'Vrindavan',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin.set_password('igfadmin123')
        admin.save()
        self.stdout.write(f'  ✅ Admin: admin@igf.org / igfadmin123')

        # ── Mentors ────────────────────────────────
        mentors_data = [
            ('Priya Menon',    'priya@igf.org',   'Mumbai'),
            ('Deepa Sharma',   'deepa@igf.org',   'Delhi'),
        ]
        mentors = []
        for name, email, city in mentors_data:
            m, _ = User.objects.get_or_create(email=email, defaults={
                'name': name, 'role': 'mentor', 'city': city,
                'mentor': None,
            })
            m.set_password('mentor123')
            m.save()
            mentors.append(m)
            self.stdout.write(f'  ✅ Mentor: {email} / mentor123')

        # ── Mentees ────────────────────────────────
        mentees_data = [
            ('Ananya Rao',     'ananya@igf.org',   'Bangalore',  mentors[0]),
            ('Sita Iyer',      'sita@igf.org',     'Chennai',    mentors[0]),
            ('Gopi Kumari',    'gopi@igf.org',     'Hyderabad',  mentors[0]),
            ('Tulsi Verma',    'tulsi@igf.org',    'Pune',       mentors[1]),
            ('Yamuna Das',     'yamuna@igf.org',   'Kolkata',    mentors[1]),
        ]
        mentees = []
        for name, email, city, mentor in mentees_data:
            u, _ = User.objects.get_or_create(email=email, defaults={
                'name': name, 'role': 'mentee', 'city': city, 'mentor': mentor,
            })
            u.set_password('mentee123')
            u.save()
            mentees.append(u)
            self.stdout.write(f'  ✅ Mentee: {email} / mentee123')

        # ── Sadhana Entries (30 days) ─────────────
        all_devotees = mentors + mentees
        today = timezone.localdate()
        entries_created = 0
        for user in all_devotees:
            for i in range(30):
                d = today - timedelta(days=i)
                if random.random() < 0.80:   # 80% submission rate
                    SadhanaEntry.objects.get_or_create(user=user, date=d, defaults={
                        'wake_up_time':     f'0{random.randint(3,5)}:{random.choice(["00","15","30","45"])}',
                        'chant_count':      random.choice([4, 8, 12, 16, 16, 16, 20]),
                        'mangal_arati':     random.random() < 0.65,
                        'hear_minutes':     random.choice([0, 15, 30, 45, 60]),
                        'read_minutes':     random.choice([0, 15, 30, 45]),
                        'service':          random.choice([
                            'Book distribution', 'Cooking prasad',
                            'Deity seva', 'Cleaning temple', 'Greeting cards',
                        ]),
                        'day_rest_minutes': random.choice([0, 30, 60]),
                    })
                    entries_created += 1
        self.stdout.write(f'  ✅ Created {entries_created} sadhana entries')

        # ── Announcements ──────────────────────────
        Announcement.objects.get_or_create(
            title='Welcome to IGF Sadhana Tracker! 🌸',
            defaults={
                'content': 'Hare Krishna! We are thrilled to launch the new IGF Sadhana Tracker. Please fill your daily sadhana every morning. Jai Radhe!',
                'posted_by': admin,
                'audience': 'all',
            }
        )
        Announcement.objects.get_or_create(
            title='Ekadashi Reminder 🪔',
            defaults={
                'content': 'Reminder: Ekadashi fasting is this Thursday. Please increase your chanting and hearing on this auspicious day.',
                'posted_by': admin,
                'audience': 'all',
            }
        )
        self.stdout.write('  ✅ Announcements created')

        # ── Lectures ──────────────────────────────
        Lecture.objects.get_or_create(
            title='The Importance of Chanting Hare Krishna',
            defaults={
                'speaker': 'HH Radhanath Swami',
                'youtube_link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'description': 'A beautiful lecture on the power of the Holy Name.',
                'uploaded_by': admin,
            }
        )
        Lecture.objects.get_or_create(
            title='Bhagavad Gita Overview – All 18 Chapters',
            defaults={
                'speaker': 'HH Sacinandana Swami',
                'youtube_link': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'description': 'A comprehensive overview of the Bhagavad Gita As It Is.',
                'uploaded_by': admin,
            }
        )
        self.stdout.write('  ✅ Lectures created')

        self.stdout.write(self.style.SUCCESS('\n🙏 Demo seed complete! Login credentials:'))
        self.stdout.write('   Admin  → admin@igf.org     / igfadmin123')
        self.stdout.write('   Mentor → priya@igf.org     / mentor123')
        self.stdout.write('   Mentee → ananya@igf.org    / mentee123')
