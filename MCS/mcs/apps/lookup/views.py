import hashlib
import os.path

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
    # Setup pickle file path
    username = request.user.username
    pickle_name = hashlib.md5(username).hexdigest()
    pickle_path = settings.MEDIA_ROOT + '/configs/' + pickle_name + '.pickle'
    # Check if pickle file exists, load ring from it.
    # if os.path.exists(pickle_path):
    #     ring = utils.load(pickle_path)
    #     RINGS[username] = ring
    #     return redirect('home')

    if request.method == 'POST':
        form = forms.UploadCloudConfigsForm(request.POST, request.FILES)
        if form.is_valid():
            # Init Cloud objects.
            clouds = utils.load_cloud_configs(username, request.FILES['cloud_configs'])
            ring = Ring(username, clouds)
            RINGS[username] = ring
            # Temporary
            # utils.save(ring, pickle_path)
            return redirect('home')
    else:
        form = forms.UploadCloudConfigsForm()
    return render(request, 'lookup/config.html',
                  {
                      'form': form,
                      'username': request.user.username,
                  })
