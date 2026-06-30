"""
IGF (ISKCON Girls Forum) - Single Models File
All models: User, InviteToken, SadhanaEntry, Announcement, Lecture, Notification
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone



# ─────────────────────────────────────────────
#  Custom User Manager
# ─────────────────────────────────────────────
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('role', 'admin')
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


# ─────────────────────────────────────────────
#  User Model  (Admin / Mentor / Mentee)
# ─────────────────────────────────────────────
class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin',   'Admin'),
        ('mentor',  'Mentor'),
        ('mentee',  'Mentee'),
    ]

    # Core fields
    name            = models.CharField(max_length=150)
    email           = models.EmailField(unique=True)
    mobile          = models.CharField(max_length=15, unique=True, null=True, blank=True)
    date_of_birth   = models.DateField(null=True, blank=True)
    city            = models.CharField(max_length=100, blank=True)
    role            = models.CharField(max_length=10, choices=ROLE_CHOICES, default='mentee')
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)

    # Hierarchy
    mentor          = models.ForeignKey(
        'self', null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='mentees',
        limit_choices_to={'role': 'mentor'}
    )

    # Status
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        verbose_name = 'User'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.role})"

    # Convenience
    @property
    def is_admin(self):   return self.role == 'admin'
    @property
    def is_mentor(self):  return self.role == 'mentor'
    @property
    def is_mentee(self):  return self.role == 'mentee'

    def get_streak(self):
        """Return current consecutive-day submission streak."""
        entries = self.sadhana_entries.order_by('-date').values_list('date', flat=True)
        streak = 0
        check = timezone.localdate()
        for d in entries:
            if d == check:
                streak += 1
                check -= timezone.timedelta(days=1)
            elif d < check:
                break
        return streak

    def get_monthly_completion(self, year=None, month=None):
        """Return % of days in the month where sadhana was submitted."""
        from calendar import monthrange
        today = timezone.localdate()
        year  = year  or today.year
        month = month or today.month
        days_in_month  = monthrange(year, month)[1]
        submitted_days = self.sadhana_entries.filter(
            date__year=year, date__month=month
        ).count()
        return round((submitted_days / days_in_month) * 100, 1) if days_in_month else 0


# ─────────────────────────────────────────────
#  Invite Token
# ─────────────────────────────────────────────
class InviteToken(models.Model):
    ROLE_CHOICES = [('mentor', 'Mentor'), ('mentee', 'Mentee')]

    token      = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email      = models.EmailField()
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_invites')
    role       = models.CharField(max_length=10, choices=ROLE_CHOICES)
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Invite → {self.email} ({self.role})"

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────
#  Daily Sadhana Entry
# ─────────────────────────────────────────────
class SadhanaEntry(models.Model):
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sadhana_entries')
    date        = models.DateField(default=timezone.localdate)

    # Fields
    sleep_time      = models.TimeField(null=True, blank=True, help_text='Last night sleep time')
    wake_up_time    = models.TimeField(null=True, blank=True)
    chant_count     = models.PositiveSmallIntegerField(default=0, help_text='Number of rounds')
    mangal_arati    = models.BooleanField(default=False)
    hear_minutes    = models.PositiveSmallIntegerField(default=0, help_text='Hearing & thinking (min)')
    read_minutes    = models.PositiveSmallIntegerField(default=0, help_text='Reading & thinking (min)')
    service         = models.CharField(max_length=255, blank=True, help_text='Type of seva/service')
    day_rest_minutes = models.PositiveSmallIntegerField(default=0, help_text='Rest / nap (min)')
    notes           = models.TextField(blank=True)

    # Meta
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']
        verbose_name = 'Sadhana Entry'
        verbose_name_plural = 'Sadhana Entries'

    def __str__(self):
        return f"{self.user.name} – {self.date}"

    @property
    def is_complete(self):
        """Entry with chanting and either reading or hearing counts as complete."""
        return self.chant_count > 0 and (self.read_minutes > 0 or self.hear_minutes > 0)

    @property
    def completion_label(self):
        if self.chant_count >= 16 and self.mangal_arati:
            return 'complete'
        if self.chant_count > 0:
            return 'partial'
        return 'minimal'


# ─────────────────────────────────────────────
#  Announcement
# ─────────────────────────────────────────────
class Announcement(models.Model):
    AUDIENCE_CHOICES = [
        ('all',     'Everyone'),
        ('mentors', 'Mentors Only'),
        ('mentees', 'Mentees Only'),
    ]

    title      = models.CharField(max_length=200)
    content    = models.TextField()
    image      = models.ImageField(upload_to='announcements/', null=True, blank=True)
    attachment = models.FileField(upload_to='announcements/', null=True, blank=True)
    posted_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='announcements')
    audience   = models.CharField(max_length=10, choices=AUDIENCE_CHOICES, default='all')
    # Mentor-specific audience (null = visible to all mentees of that mentor)
    for_mentor = models.ForeignKey(
        User, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='mentor_announcements',
        limit_choices_to={'role': 'mentor'}
    )
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


# ─────────────────────────────────────────────
#  Lecture
# ─────────────────────────────────────────────
class Lecture(models.Model):
    title        = models.CharField(max_length=200)
    speaker      = models.CharField(max_length=150)
    youtube_link = models.URLField()
    description  = models.TextField(blank=True)
    uploaded_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lectures')
    is_active    = models.BooleanField(default=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} – {self.speaker}"

    @property
    def youtube_embed(self):
        import re
        yt = self.youtube_link
        print(f"DEBUG youtube_link: {yt}")  # check your terminal/logs
        vid = None
        patterns = [
            r'youtu\.be/([^?&]+)',
            r'youtube\.com/watch\?v=([^&]+)',
            r'youtube\.com/embed/([^?&]+)',
        ]
        for p in patterns:
            m = re.search(p, yt)
            if m:
                vid = m.group(1)
                break
        result = f"https://www.youtube.com/embed/{vid}?rel=0" if vid else yt
        print(f"DEBUG embed result: {result}")  # check what's being generated
        return result
# ─────────────────────────────────────────────
#  Notification (in-app)
# ─────────────────────────────────────────────
class Notification(models.Model):
    TYPE_CHOICES = [
        ('info',    'Info'),
        ('warning', 'Warning'),
        ('success', 'Success'),
    ]

    recipient   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message     = models.CharField(max_length=300)
    notif_type  = models.CharField(max_length=10, choices=TYPE_CHOICES, default='info')
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"→ {self.recipient.name}: {self.message[:50]}"


class ContactMessage(models.Model):
    name       = models.CharField(max_length=150)
    mobile     = models.CharField(max_length=15)
    city       = models.CharField(max_length=100, blank=True)
    message    = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} – {self.mobile}"

