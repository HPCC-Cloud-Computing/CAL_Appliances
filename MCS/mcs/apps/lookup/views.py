import hashlib

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from lookup import forms
from lookup import utils
from lookup.chord.ring import Ring

from mcs.wsgi import RINGS


@login_required(login_url='/auth/login/')
def init_ring(request):
    """Init Ring per user"""
    if request.method == 'POST':
        form = forms.UploadCloudConfigsForm(request.POST, request.FILES)
        if form.is_valid():
            username = request.user.username
            # Init Cloud objects.
            clouds = utils.load_cloud_configs(username, request.FILES['cloud_configs'])

            ring = Ring(username, clouds)
            RINGS[username] = ring

            # Write json to file
            file_name = hashlib.md5(username).hexdigest()
            # Temporary
            utils.save(ring, settings.MEDIA_ROOT + '/configs/' + file_name + '.pickle')
            return redirect('home')
    else:
        form = forms.UploadCloudConfigsForm()
    return render(request, 'lookup/config.html',
                  {
                      'form': form,
                      'username': request.user.username,
                  })
