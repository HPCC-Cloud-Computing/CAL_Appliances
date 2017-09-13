# from django.views.generic import TemplateView
# from django.shortcuts import redirect
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
# from django.urls import reverse
from django.db.models import Q
from django.shortcuts import *
from django.contrib import messages
from django.db import transaction
from django.contrib.auth.models import Permission
from .forms import UserForm, UserProfileForm, LoginForm
from .models import UserProfile, Role


class ViewMessage:
    def __init__(self, message_type, title, content):
        self.message_type = message_type
        self.title = title
        self.content = content


def login_user(request):
    if request.method == "GET":
        login_form = LoginForm()
        return render(request, 'authentication/login.html',
                      context={'login_form': login_form, })

    if request.method == "POST":
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name_email = login_form.cleaned_data['user_name_email']
            user = User.objects.filter(
                Q(username=user_name_email) | Q(email=user_name_email)).first()
            # if user is admin
            login(request, user)
            return redirect(reverse('admin:index'))
            # if user is normal user
        else:
            messages.error(request, 'Invalid user name, email or password.',
                           extra_tags='danger')  # <-
            return render(request, 'authentication/login.html',
                          context={'login_form': login_form, })


@transaction.atomic
def register_user(request):
    if request.method == 'GET':
        user_form = UserForm()
        user_profile_form = UserProfileForm()
        return render(request, 'authentication/register.html',
                      context={'user_form': user_form,
                               'user_profile_form': user_profile_form})
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        user_profile_form = UserProfileForm(request.POST)
        if user_form.is_valid() and user_profile_form.is_valid():
            user = User(
                username=user_form.cleaned_data['user_name'],
                email=user_form.cleaned_data['email'],
            )
            user.set_password(user_form.cleaned_data['password'], )
            user.save()
            user_permission = Permission.objects.filter(
                codename='user_role').first()
            user.user_permissions.add(user_permission)
            user.save()
            user_profile = UserProfile(
                user=user,
                company=user_profile_form.cleaned_data['company'])
            user_profile.save()
            user_role = Role.objects.filter(role_name='user').first()
            user_profile.roles.add(user_role)
            user_profile.save()
            messages.success(request, 'Registration successful, '
                                      'please login to access your dashboard.',
                             extra_tags='success')
            return redirect(reverse('auth:login'))
        else:
            messages.error(request, 'Invalid input, check your form again.',
                           extra_tags='danger')  # <-
            return render(request, 'authentication/register.html',
                          context={
                              'user_form': user_form,
                              'user_profile_form': user_profile_form,
                          })


@require_POST
def user_exists(request):
    user_count = User.objects.filter(
        username=request.POST.get('username')).count()
    if user_count == 0:
        return False
    return True


def logout_view(request):
    logout(request)
    return redirect(reverse('admin:index'))
