from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render

from dashboard.forms import UserForm, UserProfileForm


@login_required(login_url='/auth/login')
def show_user(request):
    return render(request, 'dashboard/user.html')


@login_required(login_url='/auth/login/')
@transaction.atomic
def update_user(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, request.FILES,
                             instance=request.user)
        profile_form = UserProfileForm(request.POST,
                                       request.FILES,
                                       instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    return render(request, 'dashboard/user.html',
                  {'user_form': user_form,
                   'profile_form': profile_form})
