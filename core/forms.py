"""
IGF – Single Forms File
All forms: Login, Register, InviteUser, SadhanaEntry, Announcement, Lecture
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone
from .models import User, InviteToken, SadhanaEntry, Announcement, Lecture


# ─────────────────────────────────────────────
#  Login Form
# ─────────────────────────────────────────────
class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'your@email.com',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': '••••••••',
        })
    )


# ─────────────────────────────────────────────
#  Registration Form  (used by invited users)
# ─────────────────────────────────────────────
class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Choose a password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat password'})
    )

    class Meta:
        model = User
        fields = ['name', 'email', 'mobile', 'date_of_birth', 'city']
        widgets = {
            'name':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name'}),
            'email':         forms.EmailInput(attrs={'class': 'form-control', 'readonly': True}),
            'mobile':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'city':          forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Your city'}),
        }

    def clean(self):
        cd = super().clean()
        p1, p2 = cd.get('password1'), cd.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Passwords do not match.')
        return cd

    def save(self, role='mentee', mentor=None, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role   = role
        user.mentor = mentor
        if commit:
            user.save()
        return user


# ─────────────────────────────────────────────
#  Invite Form  (Admin invites mentor / Mentor invites mentee)
# ─────────────────────────────────────────────
class InviteForm(forms.Form):
    name  = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Invitee name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Invitee email'})
    )

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        active_invite = InviteToken.objects.filter(
            email=email, is_used=False,
            expires_at__gt=timezone.now()
        ).exists()
        if active_invite:
            raise forms.ValidationError('An active invite has already been sent to this email.')
        return email


# ─────────────────────────────────────────────
#  Sadhana Entry Form
# ─────────────────────────────────────────────
class SadhanaForm(forms.ModelForm):
    class Meta:
        model  = SadhanaEntry
        fields = [
            'date', 'sleep_time', 'wake_up_time',
            'chant_count', 'mangal_arati',
            'hear_minutes', 'read_minutes',
            'service', 'day_rest_minutes', 'notes',
        ]
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type':  'date',
            }),
            'sleep_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type':  'time',
            }),
            'wake_up_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type':  'time',
            }),
            'chant_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   '0',
                'max':   '64',
                'placeholder': '0',
            }),
            'mangal_arati': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role':  'switch',
            }),
            'hear_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   '0',
                'placeholder': '0',
            }),
            'read_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   '0',
                'placeholder': '0',
            }),
            'service': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. Book distribution, Cooking prasad…',
            }),
            'day_rest_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min':   '0',
                'placeholder': '0',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows':  3,
                'placeholder': 'Any additional notes…',
            }),
        }
        labels = {
            'chant_count':      'Chanting (rounds)',
            'mangal_arati':     'Attended Mangal Arati?',
            'hear_minutes':     'Hearing & Thinking (min)',
            'read_minutes':     'Reading & Thinking (min)',
            'day_rest_minutes': 'Rest / Nap (min)',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Default date to today
        if not self.instance.pk:
            self.fields['date'].initial = timezone.localdate()

    def clean(self):
        cd = super().clean()
        date = cd.get('date')
        if date and date > timezone.localdate():
            self.add_error('date', 'You cannot submit sadhana for a future date.')
        if self.user and date:
            qs = SadhanaEntry.objects.filter(user=self.user, date=date)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('date', 'You have already submitted sadhana for this date.')
        return cd


# ─────────────────────────────────────────────
#  Announcement Form
# ─────────────────────────────────────────────
class AnnouncementForm(forms.ModelForm):
    class Meta:
        model  = Announcement
        fields = ['title', 'content', 'image', 'attachment', 'audience']
        widgets = {
            'title':    forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Announcement title'}),
            'content':  forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'image':    forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx'}),
            'audience': forms.Select(attrs={'class': 'form-select'}),
        }


# ─────────────────────────────────────────────
#  Lecture Form
# ─────────────────────────────────────────────
class LectureForm(forms.ModelForm):
    class Meta:
        model  = Lecture
        fields = ['title', 'speaker', 'youtube_link', 'description']
        widgets = {
            'title':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lecture title'}),
            'speaker':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Speaker name'}),
            'youtube_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://youtube.com/watch?v=…'}),
            'description':  forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


# ─────────────────────────────────────────────
#  Profile Edit Form
# ─────────────────────────────────────────────
class ProfileForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = ['name', 'mobile', 'date_of_birth', 'city', 'profile_picture']
        widgets = {
            'name':          forms.TextInput(attrs={'class': 'form-control'}),
            'mobile':        forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'city':          forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }


# ─────────────────────────────────────────────
#  Report Filter Form  (not a model form)
# ─────────────────────────────────────────────
class ReportFilterForm(forms.Form):
    name      = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control form-control-sm',
        'placeholder': 'Search by name...'
    }))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control form-control-sm',
        'type': 'date'
    }))
    date_to   = forms.DateField(required=False, widget=forms.DateInput(attrs={
        'class': 'form-control form-control-sm',
        'type': 'date'
    }))