from __future__ import absolute_import
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
# from mcos.settings.mcos_conf import MCOS_CLUSTER_NAME


def index(request):
    return render(request, 'admin/index.html')
