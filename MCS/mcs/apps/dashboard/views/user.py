from dashboard.forms import UserForm, UserProfileForm
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect

@login_required(login_url='/auth/login')
def show_user(request):
    return render(request, 'dashboard/user.html')

@login_required(login_url='/auth/login/')
@transaction.atomic
def update_user(request):
    if request.POST == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            # return redirect('show_user')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    return render(request, 'dashboard/user.html',
                  {'user_form': user_form,
                   'profile_form': profile_form})
