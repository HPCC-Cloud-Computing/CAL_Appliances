# from django.views.generic import TemplateView
# from django.shortcuts import redirect
import json
import django
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, reverse, redirect, render_to_response
from django.contrib import messages


def permission_denied(request):
    '''
    Default view for error 403: Inadequate permissions.
    '''
    return render_to_response('handle_exceptions/403.html',status=403)
