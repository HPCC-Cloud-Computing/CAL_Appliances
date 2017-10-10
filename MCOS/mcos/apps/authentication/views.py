# from django.views.generic import TemplateView
# from django.shortcuts import redirect
import json
import django
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, reverse, redirect
from django.contrib import messages
from .forms import LoginForm, UserRegisterForm
from .auth_plugins.keystone_auth import KeyStoneClient, ClientException


class ViewMessage:
    def __init__(self, message_type, title, content):
        self.message_type = message_type
        self.title = title
        self.content = content


def login_user(request):
    if request.method == "GET":
        next_url = request.GET.get('next')
        login_form = LoginForm(initial={'next_url': next_url})
        # if next_url is not None:
        #     context['next_url']=next_url
        return render(request, 'authentication/login.html',
                      context={'login_form': login_form})

    if request.method == "POST":
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name = login_form.cleaned_data['user_name']
            password = login_form.cleaned_data['password']
            try:
                auth_client = KeyStoneClient(user_name=user_name,
                                             password=password)
                auth_token = auth_client.session.get_token()
                request.session['auth_token'] = auth_token
                next_url = login_form.cleaned_data['next_url']
                if len(next_url) > 0:
                    return redirect(next_url)
                else:
                    if auth_client.has_role('admin'):
                        return redirect(reverse('admin:dashboard'))
                    else:
                        return redirect(reverse('user:dashboard'))
            except ClientException as e:
                print(e)
                messages.error(request, 'Invalid user name or password.',
                               extra_tags='danger')
                return render(request, 'authentication/login.html',
                              context={'login_form': login_form, }, status=403)
        else:
            messages.error(request, 'Invalid user name, email or password.',
                           extra_tags='danger')
            return render(request, 'authentication/login.html',
                          context={'login_form': login_form, }, status=403)


def api_login(request):
    if request.method == "GET":
        login_form = LoginForm()
        return JsonResponse(
            {'csrftoken': django.middleware.csrf.get_token(request)})

    if request.method == "POST":
        login_form = LoginForm(request.POST)
        if login_form.is_valid():
            user_name_email = login_form.cleaned_data['user_name_email']
            user = User.objects.filter(
                Q(username=user_name_email) | Q(email=user_name_email)).first()
            # if user is admin
            login(request, user)
            login_result = {'is_authenticate': 'true'}
            return HttpResponse(json.dumps(login_result),
                                content_type="application/json", status=200)
            # if user is normal user
        else:
            login_result = {'is_authenticate': 'false',
                            'reason': 'invalid username or password'}

            return HttpResponse(json.dumps(login_result),
                                content_type="application/json", status=403)


def register_user(request):
    if request.method == 'GET':
        register_form = UserRegisterForm()
        return render(request, 'authentication/register.html',
                      context={'register_form': register_form, })
    if request.method == 'POST':
        register_form = UserRegisterForm(request.POST)
        if register_form.is_valid():
            try:
                user_name = register_form.cleaned_data['user_name']
                password = register_form.cleaned_data['password']
                KeyStoneClient.create_user(user_name, password)
                messages.success(request, 'Registration successful, '
                                          'please login to access '
                                          'your dashboard.',
                                 extra_tags='success')
                return redirect(reverse('auth:login'))
            except ClientException as e:
                messages.error(request, str(e), extra_tags='danger')
                return render(request, 'authentication/register.html',
                              context={'register_form': register_form, })

        else:
            messages.error(request, 'Invalid input, check your form again.',
                           extra_tags='danger')
            return render(request, 'authentication/register.html',
                          context={'register_form': register_form, })


@require_POST
def user_exists(request):
    user_count = User.objects.filter(
        username=request.POST.get('username')).count()
    if user_count == 0:
        return False
    return True


def logout_view(request):
    logout(request)
    return redirect(reverse('auth:login'))
