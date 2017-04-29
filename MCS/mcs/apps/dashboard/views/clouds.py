import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse

from lookup import utils
from mcs.wsgi import RINGS


@login_required(login_url='/auth/login/')
def list_clouds(request):
    username = request.user.username
    ring = RINGS[username]
    clouds = ring.clouds
    for cloud in clouds:
        utils.set_usage_cloud(cloud)
        cloud.set_used_rate()

    return render(request, 'dashboard/clouds.html',
                  {
                      'clouds': clouds,
                  })


@login_required(login_url='/auth/login/')
def update_cloud(request):
    cloud_name = request.GET.get('cloud_name')
    # user name to get rate and status
    username = request.user.username
    ring = RINGS[username]
    clouds = ring.clouds
    cloud = [c for c in clouds if c.name == cloud_name][0]
    # Re get metric
    cloud.set_used_rate()
    cloud.check_health()

    result = {
        'rate': cloud.used_rate,
        'status': cloud.status,
    }
    return JsonResponse(result)
