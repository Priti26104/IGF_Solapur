"""
IGF – All Views
"""

import csv
import io
import json
from datetime import date, timedelta
from calendar import monthrange

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Avg, Count, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.conf import settings

from .models import User, InviteToken, SadhanaEntry, Announcement, Lecture, Notification
from .forms import (
    LoginForm, RegisterForm, InviteForm,
    SadhanaForm, AnnouncementForm, LectureForm,
    ProfileForm, ReportFilterForm,
)
from .decorators import admin_required, mentor_required, mentee_required, mentor_or_admin


# ══════════════════════════════════════════════
#  AUTH VIEWS
# ══════════════════════════════════════════════

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        messages.success(request, f'Welcome back, {form.get_user().name}! 🙏')
        return redirect(request.GET.get('next', 'dashboard'))
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out. Hare Krishna! 🙏')
    return redirect('login')


def register_view(request):
    token_str = request.GET.get('token') or request.POST.get('token')
    token = get_object_or_404(InviteToken, token=token_str)

    if not token.is_valid:
        messages.error(request, 'This invite link has expired or already been used.')
        return redirect('login')

    form = RegisterForm(request.POST or None, initial={'email': token.email})

    if request.method == 'POST' and form.is_valid():
        mentor = token.invited_by if token.role == 'mentee' else None
        user = form.save(role=token.role, mentor=mentor)
        token.is_used = True
        token.save()
        # Notify inviter
        Notification.objects.create(
            recipient=token.invited_by,
            message=f'{user.name} has registered as a {user.role}.',
            notif_type='success'
        )
        login(request, user)
        messages.success(request, f'Welcome to IGF, {user.name}! Hare Krishna 🙏')
        return redirect('dashboard')

    return render(request, 'accounts/register.html', {'form': form, 'token': token_str})


# ══════════════════════════════════════════════
#  DASHBOARD  (role-based)
# ══════════════════════════════════════════════

@login_required
def dashboard(request):
    user = request.user
    if user.is_admin:
        return admin_dashboard(request)
    elif user.is_mentor:
        return mentor_dashboard(request)
    else:
        return mentee_dashboard(request)


def admin_dashboard(request):
    today = timezone.localdate()
    total_devotees = User.objects.filter(is_active=True).count()
    total_mentors  = User.objects.filter(role='mentor', is_active=True).count()
    total_mentees  = User.objects.filter(role='mentee', is_active=True).count()
    today_entries  = SadhanaEntry.objects.filter(date=today).count()
    pending        = total_mentees - SadhanaEntry.objects.filter(date=today, user__role='mentee').count()
    avg_chanting   = SadhanaEntry.objects.filter(date=today).aggregate(a=Avg('chant_count'))['a'] or 0

    # 7-day trend
    trend_labels, trend_data = [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        cnt = SadhanaEntry.objects.filter(date=d).count()
        trend_labels.append(d.strftime('%b %d'))
        trend_data.append(cnt)

    # Recent registrations
    recent_users = User.objects.order_by('-created_at')[:5]
    notifications = request.user.notifications.filter(is_read=False)[:5]

    ctx = {
        'total_devotees': total_devotees,
        'total_mentors': total_mentors,
        'total_mentees': total_mentees,
        'today_entries': today_entries,
        'pending': pending,
        'avg_chanting': round(avg_chanting, 1),
        'trend_labels': json.dumps(trend_labels),
        'trend_data':   json.dumps(trend_data),
        'recent_users': recent_users,
        'notifications': notifications,
        'unread_count': notifications.count(),
    }
    return render(request, 'admin_panel/dashboard.html', ctx)


def mentor_dashboard(request):
    user  = request.user
    today = timezone.localdate()
    mentees = user.mentees.filter(is_active=True)
    submitted_today = SadhanaEntry.objects.filter(date=today, user__in=mentees).count()
    pending = mentees.count() - submitted_today
    avg_chant = SadhanaEntry.objects.filter(
        date=today, user__in=mentees
    ).aggregate(a=Avg('chant_count'))['a'] or 0

    today_entry = SadhanaEntry.objects.filter(user=user, date=today).first()
    notifications = user.notifications.filter(is_read=False)[:5]

    ctx = {
        'mentees': mentees,
        'mentees_count': mentees.count(),
        'submitted_today': submitted_today,
        'pending': pending,
        'avg_chant': round(avg_chant, 1),
        'today_entry': today_entry,
        'notifications': notifications,
        'unread_count': notifications.count(),
        'streak': user.get_streak(),
    }
    return render(request, 'mentor/dashboard.html', ctx)


def mentee_dashboard(request):
    user  = request.user
    today = timezone.localdate()
    today_entry   = SadhanaEntry.objects.filter(user=user, date=today).first()
    streak        = user.get_streak()
    monthly_pct   = user.get_monthly_completion()
    total_chanting = user.sadhana_entries.aggregate(s=Count('chant_count'))['s'] or 0
    mangal_entries = user.sadhana_entries.filter(mangal_arati=True).count()
    total_entries  = user.sadhana_entries.count()
    mangal_pct = round((mangal_entries / total_entries) * 100, 1) if total_entries else 0

    # 30-day reading/hearing trend
    trend_labels, read_data, hear_data = [], [], []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        e = user.sadhana_entries.filter(date=d).first()
        trend_labels.append(d.strftime('%d'))
        read_data.append(e.read_minutes if e else 0)
        hear_data.append(e.hear_minutes if e else 0)

    announcements = Announcement.objects.filter(
        is_active=True
    ).exclude(audience='mentors')[:5]
    notifications = user.notifications.filter(is_read=False)[:5]

    ctx = {
        'today_entry': today_entry,
        'streak': streak,
        'monthly_pct': monthly_pct,
        'total_chanting': total_chanting,
        'mangal_pct': mangal_pct,
        'trend_labels': json.dumps(trend_labels),
        'read_data':   json.dumps(read_data),
        'hear_data':   json.dumps(hear_data),
        'announcements': announcements,
        'notifications': notifications,
        'unread_count': notifications.count(),
    }
    return render(request, 'mentee/dashboard.html', ctx)


# ══════════════════════════════════════════════
#  SADHANA VIEWS
# ══════════════════════════════════════════════

@login_required
def sadhana_form(request):
    today = timezone.localdate()
    existing = SadhanaEntry.objects.filter(user=request.user, date=today).first()
    form = SadhanaForm(
        request.POST or None,
        instance=existing,
        user=request.user
    )
    if request.method == 'POST' and form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.save()
        messages.success(request, 'Sadhana submitted! Hare Krishna! 🌸')
        return redirect('dashboard')
    return render(request, 'sadhana/form.html', {
        'form': form, 'existing': existing
    })


@login_required
def sadhana_calendar(request, user_id=None):
    if user_id:
        target = get_object_or_404(User, pk=user_id)
        # permission check
        if not (request.user.is_admin or
                (request.user.is_mentor and target.mentor == request.user) or
                request.user == target):
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
    else:
        target = request.user

    today = timezone.localdate()
    year  = int(request.GET.get('year',  today.year))
    month = int(request.GET.get('month', today.month))

    entries = {
        e.date: e.completion_label
        for e in target.sadhana_entries.filter(date__year=year, date__month=month)
    }

    # Build calendar grid
    first_day = date(year, month, 1)
    days_count = monthrange(year, month)[1]
    # pad start
    start_pad = first_day.weekday()  # Mon=0
    cal_days = [None] * start_pad + [date(year, month, d) for d in range(1, days_count + 1)]

    prev_month = (first_day - timedelta(days=1)).replace(day=1)
    next_month_d = date(year, month, days_count) + timedelta(days=1)

    ctx = {
        'target': target,
        'year': year, 'month': month,
        'month_name': first_day.strftime('%B %Y'),
        'cal_days': cal_days,
        'entries': entries,
        'today': today,
        'prev_year': prev_month.year, 'prev_month': prev_month.month,
        'next_year': next_month_d.year, 'next_month': next_month_d.month,
    }
    return render(request, 'sadhana/calendar.html', ctx)


@login_required
def sadhana_detail(request, user_id, entry_date):
    target = get_object_or_404(User, pk=user_id)
    entry  = get_object_or_404(SadhanaEntry, user=target, date=entry_date)
    if not (request.user.is_admin or
            (request.user.is_mentor and target.mentor == request.user) or
            request.user == target):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    return render(request, 'sadhana/detail.html', {'entry': entry, 'target': target})


# ══════════════════════════════════════════════
#  INVITE VIEWS
# ══════════════════════════════════════════════
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings

from .forms import InviteForm
from .models import InviteToken


from django.core.mail import EmailMultiAlternatives
from django.conf import settings

@login_required
def send_invite(request):
    user = request.user

    if not (user.is_admin or user.is_mentor):
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    role = "mentor" if user.is_admin else "mentee"
    form = InviteForm(request.POST or None)

    if request.method == "POST":

        if form.is_valid():

            email = form.cleaned_data["email"]
            name = form.cleaned_data.get("name")

            try:
                invite = InviteToken.objects.create(
                    email=email,
                    invited_by=user,
                    role=role
                )

                reg_url = f"{settings.SITE_URL}/register/?token={invite.token}"

                subject = "🌸 You're Invited to Join IGF Sadhana Tracker"

                text_content = f"""
Hare Krishna!

{name},

You have been invited to join the ISKCON Girls Forum (IGF) Sadhana Tracker as a {role}.

Register here:
{reg_url}

This invitation is valid for 7 days.

Hare Krishna 🙏
IGF Team
"""

                html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
</head>
<body style="margin:0;padding:0;background:#FFF8FB;font-family:Arial,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#FFF8FB;padding:30px 0;">
<tr>
<td align="center">

<table width="600" cellpadding="0" cellspacing="0"
style="background:#ffffff;border-radius:16px;overflow:hidden;
box-shadow:0 5px 20px rgba(0,0,0,0.08);">

<tr>
<td style="background:#FCE4EC;padding:30px;text-align:center;">
<h1 style="margin:0;color:#C2185B;">
🌸 IGF Sadhana Tracker
</h1>
<p style="margin-top:10px;color:#6D4C41;">
ISKCON Girls Forum
</p>
</td>
</tr>

<tr>
<td style="padding:35px;">

<h2 style="color:#C2185B;margin-top:0;">
Hare Krishna, {name}! 🙏
</h2>

<p style="font-size:15px;color:#444;line-height:1.7;">
You have been invited to join the
<strong>ISKCON Girls Forum (IGF) Sadhana Tracker</strong>
as a <strong>{role.title()}</strong>.
</p>

<p style="font-size:15px;color:#444;line-height:1.7;">
Use the button below to complete your registration.
</p>

<div style="text-align:center;margin:35px 0;">
<a href="{reg_url}"
style="
background:#E91E63;
color:white;
text-decoration:none;
padding:14px 32px;
border-radius:8px;
font-weight:bold;
font-size:16px;
display:inline-block;
">
Register Now
</a>
</div>

<p style="font-size:14px;color:#666;">
⏳ This invitation link is valid for <strong>7 days</strong>.
</p>

<p style="font-size:14px;color:#666;">
If the button does not work, copy and paste this link into your browser:
</p>

<p style="word-break:break-all;color:#E91E63;font-size:13px;">
{reg_url}
</p>

</td>
</tr>

<tr>
<td style="background:#FCE4EC;padding:20px;text-align:center;">
<p style="margin:0;color:#6D4C41;font-size:13px;">
Hare Krishna 🙏<br>
IGF Sadhana Tracker Team
</p>
</td>
</tr>

</table>

</td>
</tr>
</table>

</body>
</html>
"""

                email_message = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.EMAIL_HOST_USER,
                    to=[email],
                )

                email_message.attach_alternative(
                    html_content,
                    "text/html"
                )

                email_message.send()

                messages.success(
                    request,
                    f"Invitation sent successfully to {email} 🌸"
                )

            except Exception as e:
                messages.error(
                    request,
                    f"Email failed: {str(e)}"
                )

            return redirect("invite_list")

    invites = InviteToken.objects.filter(
        invited_by=user
    ).order_by("-created_at")[:20]

    return render(
        request,
        "accounts/invite.html",
        {
            "form": form,
            "invites": invites,
            "role": role,
        }
    )


@login_required
def invite_list(request):
    if request.user.is_admin:
        invites = InviteToken.objects.all().order_by("-created_at")
    else:
        invites = InviteToken.objects.filter(
            invited_by=request.user
        ).order_by("-created_at")

    return render(
        request,
        "accounts/invite_list.html",
        {"invites": invites}
    )

# @login_required
# def send_invite(request):
#     user = request.user
#     if not (user.is_admin or user.is_mentor):
#         messages.error(request, 'Access denied.')
#         return redirect('dashboard')

#     role = 'mentor' if user.is_admin else 'mentee'
#     form = InviteForm(request.POST or None)

#     if request.method == 'POST' and form.is_valid():
#         email = form.cleaned_data['email']
#         invite = InviteToken.objects.create(
#             email=email,
#             invited_by=user,
#             role=role
#         )
#         reg_url = f"{settings.SITE_URL}/register/?token={invite.token}"
#         try:
#             send_mail(
#                 subject='You are invited to IGF Sadhana Tracker 🌸',
#                 message=f"""
# Hare Krishna!

# You have been invited to join the ISKCON Girls Forum (IGF) Sadhana Tracker as a {role}.

# Please click the link below to register:
# {reg_url}

# This link is valid for 7 days.

# Jai Radhe! 🙏
# IGF Team
#                 """,
#                 from_email=settings.DEFAULT_FROM_EMAIL,
#                 recipient_list=[email],
#                 fail_silently=False,
#             )
#             messages.success(request, f'Invitation sent to {email}! 🌸')
#         except Exception as e:
#             messages.warning(request, f'Invite created but email failed: {e}. Share this link: {reg_url}')
#         return redirect('invite_list')

#     invites = InviteToken.objects.filter(invited_by=user).order_by('-created_at')[:20]
#     return render(request, 'accounts/invite.html', {
#         'form': form, 'invites': invites, 'role': role
#     })


# @login_required
# def invite_list(request):
#     if request.user.is_admin:
#         invites = InviteToken.objects.all().order_by('-created_at')
#     else:
#         invites = InviteToken.objects.filter(invited_by=request.user).order_by('-created_at')
#     return render(request, 'accounts/invite_list.html', {'invites': invites})


# ══════════════════════════════════════════════
#  MENTOR VIEWS  (admin sees all)
# ══════════════════════════════════════════════

@login_required
@admin_required
def mentor_list(request):
    q = request.GET.get('q', '')
    mentors = User.objects.filter(role='mentor', is_active=True)
    if q:
        mentors = mentors.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(city__icontains=q))
    for m in mentors:
        m.mentee_count = m.mentees.filter(is_active=True).count()
        today = timezone.localdate()
        m.submitted_today = SadhanaEntry.objects.filter(user=m, date=today).exists()
    return render(request, 'admin_panel/mentors.html', {'mentors': mentors, 'q': q})


@login_required
def mentee_list(request):
    user = request.user
    q = request.GET.get('q', '')
    if user.is_admin:
        mentees = User.objects.filter(role='mentee', is_active=True)
    elif user.is_mentor:
        mentees = user.mentees.filter(is_active=True)
    else:
        return redirect('dashboard')
    if q:
        mentees = mentees.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(city__icontains=q))
    today = timezone.localdate()
    for m in mentees:
        m.submitted_today = SadhanaEntry.objects.filter(user=m, date=today).exists()
        m.streak = m.get_streak()
        m.monthly_pct = m.get_monthly_completion()
    return render(request, 'common/mentee_list.html', {'mentees': mentees, 'q': q})


@login_required
def hierarchy_view(request):
    if not request.user.is_admin:
        messages.error(request, 'Admin only.')
        return redirect('dashboard')
    mentors = User.objects.filter(role='mentor', is_active=True).prefetch_related('mentees')
    return render(request, 'admin_panel/hierarchy.html', {'mentors': mentors})


# ══════════════════════════════════════════════
#  REPORTS
# ══════════════════════════════════════════════

@login_required
def reports_view(request):
    user = request.user

    # Base queryset with related data
    entries = SadhanaEntry.objects.select_related('user', 'user__mentor')

    # ── Role-based scoping ──────────────────────────────
    if user.is_mentor:
        # Mentor sees only their mentees
        entries = entries.filter(user__mentor=user)

    elif user.is_mentee:
        # Mentee sees only their own entries
        entries = entries.filter(user=user)

    # Admin sees everything — no filter applied here

    # ── Filter Form ─────────────────────────────────────
    form = ReportFilterForm(request.GET or None)

    if form.is_valid():
        name      = form.cleaned_data.get('name')
        date_from = form.cleaned_data.get('date_from')
        date_to   = form.cleaned_data.get('date_to')

        if name:
            # Search by user name (case-insensitive, partial match)
            entries = entries.filter(user__name__icontains=name)

        if date_from:
            entries = entries.filter(date__gte=date_from)

        if date_to:
            entries = entries.filter(date__lte=date_to)

    entries = entries.order_by('-date')

    # ── CSV Export ───────────────────────────────────────
    if 'export_csv' in request.GET:
        return export_csv(entries)

    return render(request, 'common/reports.html', {
        'form': form,
        'entries': entries,
    })
def export_csv(entries):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="igf_sadhana_report.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Name', 'Email', 'Mentor', 'City', 'Date',
        'Wake Up', 'Chanting Rounds', 'Mangal Arati',
        'Hearing (min)', 'Reading (min)', 'Service', 'Notes'
    ])
    for e in entries:
        writer.writerow([
            e.user.name, e.user.email,
            e.user.mentor.name if e.user.mentor else '',
            e.user.city, e.date,
            e.wake_up_time or '', e.chant_count,
            'Yes' if e.mangal_arati else 'No',
            e.hear_minutes, e.read_minutes,
            e.service, e.notes,
        ])
    return response


# ══════════════════════════════════════════════
#  ANNOUNCEMENTS
# ══════════════════════════════════════════════

@login_required
def announcements_view(request):
    user = request.user
    if user.is_admin:
        anns = Announcement.objects.filter(is_active=True)
    elif user.is_mentor:
        anns = Announcement.objects.filter(
            is_active=True
        ).filter(Q(audience='all') | Q(audience='mentors') | Q(for_mentor=user))
    else:
        anns = Announcement.objects.filter(
            is_active=True
        ).filter(
            Q(audience='all') | Q(audience='mentees')
        ).filter(
            Q(for_mentor__isnull=True) | Q(for_mentor=user.mentor)
        )
    return render(request, 'common/announcements.html', {'announcements': anns})


@login_required
def create_announcement(request):
    if not (request.user.is_admin or request.user.is_mentor):
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    form = AnnouncementForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        ann = form.save(commit=False)
        ann.posted_by = request.user
        if request.user.is_mentor:
            ann.for_mentor = request.user
        ann.save()
        messages.success(request, 'Announcement posted! 🌸')
        return redirect('announcements')
    return render(request, 'common/announcement_form.html', {'form': form})


# ══════════════════════════════════════════════
#  LECTURES
# ══════════════════════════════════════════════
@login_required
def lectures_view(request):
    lectures = Lecture.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'common/lectures.html', {'lectures': lectures})


def Home(request):
    lectures = Lecture.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'common/lectures.html', {'lectures': lectures})

@login_required
@admin_required
def create_lecture(request):
    form = LectureForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        lec = form.save(commit=False)
        lec.uploaded_by = request.user
        lec.save()
        messages.success(request, 'Lecture added!')
        return redirect('lectures')
    return render(request, 'common/lecture_form.html', {'form': form})


# ══════════════════════════════════════════════
#  PROFILE
# ══════════════════════════════════════════════

@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated!')
        return redirect('profile')
    return render(request, 'common/profile.html', {'form': form})


# ══════════════════════════════════════════════
#  NOTIFICATIONS  (AJAX mark read)
# ══════════════════════════════════════════════

@login_required
def mark_notifications_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})


# ══════════════════════════════════════════════
#  ANALYTICS  (Chart data API)
# ══════════════════════════════════════════════

@login_required
def analytics_data(request):
    user  = request.user
    today = timezone.localdate()
    days  = int(request.GET.get('days', 30))
    start = today - timedelta(days=days - 1)

    if user.is_admin:
        qs = SadhanaEntry.objects.filter(date__gte=start)
    elif user.is_mentor:
        qs = SadhanaEntry.objects.filter(date__gte=start, user__in=user.mentees.all())
    else:
        qs = SadhanaEntry.objects.filter(date__gte=start, user=user)

    labels, chant, reading, hearing, submissions = [], [], [], [], []
    for i in range(days):
        d = start + timedelta(days=i)
        day_qs = qs.filter(date=d)
        labels.append(d.strftime('%b %d'))
        agg = day_qs.aggregate(
            avg_chant=Avg('chant_count'),
            avg_read=Avg('read_minutes'),
            avg_hear=Avg('hear_minutes'),
            count=Count('id')
        )
        chant.append(round(agg['avg_chant'] or 0, 1))
        reading.append(round(agg['avg_read'] or 0, 1))
        hearing.append(round(agg['avg_hear'] or 0, 1))
        submissions.append(agg['count'])

    return JsonResponse({
        'labels': labels,
        'chant': chant,
        'reading': reading,
        'hearing': hearing,
        'submissions': submissions,
    })
