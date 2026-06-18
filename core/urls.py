from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Auth
    path('',       views.login_view,   name='login'),
    path('login/',  views.login_view,   name='login'),
    path('logout/',   views.logout_view,  name='logout'),
    path('register/', views.register_view, name='register'),

    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Sadhana
    path('sadhana/',                                     views.sadhana_form,    name='sadhana_form'),
    path('sadhana/calendar/',                            views.sadhana_calendar, name='sadhana_calendar'),
    path('sadhana/calendar/<int:user_id>/',              views.sadhana_calendar, name='sadhana_calendar_user'),
    path('sadhana/detail/<int:user_id>/<str:entry_date>/', views.sadhana_detail, name='sadhana_detail'),

    # Invite
    path('invite/',      views.send_invite,  name='send_invite'),
    path('invite/list/', views.invite_list,  name='invite_list'),

    # Mentors / Mentees
    path('mentors/',   views.mentor_list,   name='mentor_list'),
    path('mentees/',   views.mentee_list,   name='mentee_list'),
    path('hierarchy/', views.hierarchy_view, name='hierarchy'),

    # Reports
    path('reports/', views.reports_view, name='reports'),

    # Announcements
    path('announcements/',        views.announcements_view,   name='announcements'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),

    # Lectures
    path('lectures/',        views.lectures_view,   name='lectures'),
    path('lectures/create/', views.create_lecture, name='create_lecture'),

    # Profile
    path('profile/', views.profile_view, name='profile'),

    # API
    path('api/notifications/read/', views.mark_notifications_read, name='notif_read'),
    path('api/analytics/',          views.analytics_data,          name='analytics_data'),

    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html',
             subject_template_name='accounts/password_reset_subject.txt',
         ),
         name='password_reset'),

    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='accounts/password_reset_done.html'
         ),
         name='password_reset_done'),

    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html'
         ),
         name='password_reset_confirm'),

    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='accounts/password_reset_complete.html'
         ),
         name='password_reset_complete'),

]
