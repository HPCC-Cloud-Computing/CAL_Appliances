from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
