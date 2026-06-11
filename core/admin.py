from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, InviteToken, SadhanaEntry, Announcement, Lecture, Notification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display  = ('name', 'email', 'role', 'mentor', 'city', 'is_active', 'created_at')
    list_filter   = ('role', 'is_active', 'city')
    search_fields = ('name', 'email', 'mobile')
    ordering      = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('name', 'mobile', 'date_of_birth', 'city', 'profile_picture')}),
        ('Role & Hierarchy', {'fields': ('role', 'mentor')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('name', 'email', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(InviteToken)
class InviteTokenAdmin(admin.ModelAdmin):
    list_display  = ('email', 'role', 'invited_by', 'is_used', 'expires_at', 'created_at')
    list_filter   = ('role', 'is_used')
    search_fields = ('email',)


@admin.register(SadhanaEntry)
class SadhanaEntryAdmin(admin.ModelAdmin):
    list_display  = ('user', 'date', 'chant_count', 'mangal_arati', 'read_minutes', 'hear_minutes')
    list_filter   = ('date', 'mangal_arati')
    search_fields = ('user__name', 'user__email')
    date_hierarchy = 'date'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display  = ('title', 'posted_by', 'audience', 'is_active', 'created_at')
    list_filter   = ('audience', 'is_active')


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display  = ('title', 'speaker', 'uploaded_by', 'is_active', 'created_at')
    list_filter   = ('is_active',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('recipient', 'message', 'notif_type', 'is_read', 'created_at')
    list_filter   = ('notif_type', 'is_read')
