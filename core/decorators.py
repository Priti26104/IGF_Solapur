from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_admin:
            messages.error(request, 'Admin access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def mentor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_mentor:
            messages.error(request, 'Mentor access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def mentee_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_mentee:
            messages.error(request, 'Mentee access required.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def mentor_or_admin(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (
            request.user.is_mentor or request.user.is_admin
        ):
            messages.error(request, 'Access denied.')
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
