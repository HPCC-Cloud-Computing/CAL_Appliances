from django.shortcuts import render

from dashboard import utils as dashboard_utils
from dashboard.models import File
from lookup import utils as lookup_utils
from mcs.wsgi import RINGS


def show_home(request):
    username = request.user.username
    ring = RINGS[username]
    clouds = ring.clouds

    total_quota = 0
    total_used = 0
    number_of_cloud = 0
    # Re-calculate total used and total quota
    for cloud in clouds:
        lookup_utils.set_quota_cloud(cloud)
        lookup_utils.set_usage_cloud(cloud)
        total_quota += cloud.quota
        total_used += cloud.used
        number_of_cloud += 1
    total_files = File.objects.filter(owner=request.user).count()
    total_used = dashboard_utils.sizeof_fmt(total_used)
    total_quota = dashboard_utils.sizeof_fmt(total_quota)

    return render(request, 'dashboard/home.html',
                  {
                      'total_quota': total_quota,
                      'total_used': total_used,
                      'total_files': total_files,
                      'number_of_cloud': number_of_cloud,
                  })
