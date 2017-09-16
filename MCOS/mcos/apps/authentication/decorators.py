from functools import wraps

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.shortcuts import resolve_url
from django.utils import six
from django.utils.decorators import available_attrs
from django.utils.six.moves.urllib.parse import urlparse
from django.http import HttpResponseForbidden


def user_passes_test(test_func):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func, assigned=available_attrs(view_func))
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden()

        return _wrapped_view

    return decorator


def api_login_required(function=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

    # def check_system_is_locked(function):
    #     def wrap(request, *args, **kwargs):
    #         if SYSTEM_INFO['is_locked']:
    #             return JsonResponse({'accept_connect': 'false',
    #                                  'reason': 'System is busy, '
    #                                            'please try again later'},
    #                                 status=403)
    #         else:
    #             return function(request, *args, **kwargs)
    #     wrap.__doc__ = function.__doc__
    #     wrap.__name__ = function.__name__
    #     return wrap
