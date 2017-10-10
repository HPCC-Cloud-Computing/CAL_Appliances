from django.shortcuts import redirect, reverse
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .keystone_auth import KeyStoneClient


def login_required(role=None, login_url='/auth/login'):
    def login_decorator(func):
        def wrapper(request, *args, **kw):
            token = request.session.get('auth_token')
            if token is None:
                token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            verify_result = KeyStoneClient.verify_token_with_role(token, role)
            if verify_result == KeyStoneClient.TOKEN_SUCCESS:
                return func(request, *args, **kw)
            elif verify_result == KeyStoneClient.TOKEN_NOT_FOUND or \
                    verify_result == KeyStoneClient.TOKEN_EXPIRED:
                messages.error(request, 'Authentication Failed. '
                                        'Please login to access',
                               extra_tags='danger')
                return redirect(login_url + '?next=%s' % request.path)
            elif verify_result == KeyStoneClient.TOKEN_FAILED:
                raise PermissionDenied

        return wrapper

    return login_decorator


def api_login_required(role=None):
    def api_login_decorator(func):
        def wrapper(request, *args, **kw):
            token = request.META.get('HTTP_X_AUTH_TOKEN', None)
            verify_result = KeyStoneClient.verify_token_with_role(token, role)
            if verify_result == KeyStoneClient.TOKEN_SUCCESS:
                return func(request, *args, **kw)
            elif verify_result == KeyStoneClient.TOKEN_NOT_FOUND or \
                    verify_result == KeyStoneClient.TOKEN_EXPIRED or \
                    verify_result == KeyStoneClient.TOKEN_FAILED:
                return JsonResponse({'auth_verify': 'failed'}, status=403)

        return wrapper

    return api_login_decorator
