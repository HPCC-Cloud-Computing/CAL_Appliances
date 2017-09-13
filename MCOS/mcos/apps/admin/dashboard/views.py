from __future__ import absolute_import
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render
# from ...lookup import utils as lookup_utils
# from .. import utils as dashboard_utils


@login_required(login_url='/auth/login/')
@permission_required('authentication.admin_role', raise_exception=True)
def dashboard(request):
    return render(request, 'admin/dashboard.html', {})


def index(request):
    return render(request, 'admin/index.html', {})


@login_required(login_url='/auth/login/')
@permission_required('authentication.user_role', raise_exception=True)
def test_user_role(request):
    return render(request, 'admin_dashboard/home.html', {})

