from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST


class LoginView(TemplateView):
    template_name = 'authentication/login.html'

    def get(self, request, *args, **kwargs):
        if request.user.id:
            return redirect('/home')
        return self.render_to_response({})

    def post(self, request, *args, **kwargs):
        user = authenticate(username=request.POST['username'],
                            password=request.POST['password'])
        if user is not None:
            login(request, user)
            return redirect('/home')
        else:
            return redirect('/auth/login')


class RegisterView(TemplateView):
    template_name = 'authentication/register.html'

    def get(self, request, *args, **kwargs):
        if request.user.id:
            return redirect('/')
        return self.render_to_response({})

    def post(self, request, *args, **kwargs):
        username = request.POST.get('username')
        password = request.POST.get('password')
        firstname = request.POST.get('firstname')
        lastname = request.POST.get('lastname')
        email = request.POST.get('email')

        user = User(
            username=username,
            first_name=firstname,
            last_name=lastname,
            email=email
        )
        user.set_password(password)
        user.save()
        return redirect('/auth/login')


@require_POST
def user_exists(request):
    user_count = User.objects.filter(
        username=request.POST.get('username')).count()
    if user_count == 0:
        return False
    return True


def logout_view(request):
    logout(request)
    return redirect('/home')
