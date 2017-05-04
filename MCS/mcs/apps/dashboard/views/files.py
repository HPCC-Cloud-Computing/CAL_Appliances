import gc
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils.encoding import smart_str

from dashboard.forms import CreateFolderForm, UploadFileForm
from dashboard.models import File
from dashboard.tasks import objects


def _get_folder(request, folder_id=None, urls={}):
    """Get folder by id, create root folder
    if it doesnt exist

    Arguments:
        request {[type]}
    Keyword Arguments:
        folder_id {[type]}
        urls {list}: multi url e.x:
            {
                'rfolder': 'create_root_folder',
                'afolder': 'create_folder'
            }

    Return
        folder: folder get by id
        url:
    """
    username = request.user.username
    if not folder_id:
        folder_id = request.GET.get('folder_id')
    if not folder_id:
        folder_id = request.POST.get('folder_id')
    if folder_id:
        try:
            folder = File.objects.filter(owner__username=username).get(id=folder_id)
            url = reverse(urls['afolder'],
                          kwargs={'folder_id': folder_id})
        except File.DoesNotExist as e:
            messages.error(request, 'File doesn\'t exist: %s' % str(e))
    else:
        # Check if root doesn't exist, create it
        try:
            folder = File.objects.filter(owner__username=username).get(name='root')
        except File.DoesNotExist:
            # TODO: When we have User, set `owner` field
            # folder = File.objects.create(name='root',
            #                              is_root=True,
            #                              is_folder=True
            #                              owner=<current_user>)
            folder = File.objects.create(name='root',
                                         owner=request.user,
                                         is_root=True,
                                         is_folder=True,
                                         path='/rfolder/')
        url = reverse(urls['rfolder'])
    return (folder, url)


@login_required(login_url='/auth/login/')
def list_files(request, folder_id=None):
    folder, url_create = _get_folder(request, folder_id=folder_id,
                                     urls={
                                         'rfolder': 'create_root_folder',
                                         'afolder': 'create_folder'
                                     })
    url_upload = _get_folder(request, folder_id=folder_id,
                             urls={
                                 'rfolder': 'upload_root_file',
                                 'afolder': 'upload_file'
                             })[1]
    return render(request, 'dashboard/files.html',
                  {
                      'folder': folder,
                      'url_create': url_create,
                      'url_upload': url_upload,
                  })


@login_required(login_url='/auth/login/')
def create_folder(request, folder_id=None):
    data = dict()
    folder, url = _get_folder(request, folder_id=folder_id,
                              urls={
                                  'rfolder': 'create_root_folder',
                                  'afolder': 'create_folder'
                              })

    if request.method == 'POST':
        form = CreateFolderForm(request.POST)
        if form.is_valid():
            new_folder = form.save(commit=False)
            data['form_is_valid'] = True
            if folder.contains_file(new_folder.name):
                # TODO: Show error in form
                form._errors['name'] = form.error_class(['Folder with this \
                                                         name already exists'])
                messages.error(request, 'Folder/File with this name already exists')
            else:
                new_folder.parent = folder
                # new_folder.owner = request.user
                # '/' at the end because it is folder.
                new_folder.path = folder.path + str(new_folder.name) + '/'
                new_folder.owner = request.user
                new_folder.save()
                messages.info(request, 'Create folder successfully!')
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            data['form_is_valid'] = False
    else:
        form = CreateFolderForm()

    template_name = 'dashboard/include/partial_folder_create.html'
    data['html_form'] = render_to_string(template_name,
                                         {'form': form, 'url_create': url},
                                         request=request)
    return JsonResponse(data)


@login_required(login_url='/auth/login/')
def delete_files(request):
    # TODO: In the case, user doesn't choose anything
    #       Throw alert.
    username = request.user.username
    files = File.objects.filter(owner__username=username). \
        filter(id__in=request.POST.getlist('checked_file'))
    # Delete the files -> Done
    for file in files:
        objects.delete_file(request, file)
    files.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/auth/login/')
def upload_file(request, folder_id=None):
    data = dict()
    folder, url = _get_folder(request, folder_id,
                              urls={
                                  'rfolder': 'upload_root_file',
                                  'afolder': 'upload_file'
                              })

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            new_file = form.save(commit=False)
            new_file.name = request.FILES['content'].name
            data['form_is_valid'] = True
            if folder.contains_file(new_file.name):
                # TODO: Show error in form
                form._errors['name'] = form.error_class(['File with this \
                                                         name already exists'])
                messages.error(request, 'Folder/File with this name already exists')
            else:
                new_file.parent = folder
                # new_folder.owner = request.user
                new_file.path = folder.path + str(new_file.name)
                new_file.size = request.FILES['content'].size
                new_file.is_folder = False
                new_file.owner = request.user
                # Save file as object
                new_file_content = ContentFile(request.FILES['content'].read())
                new_file.save()
                objects.upload_file(request, new_file, new_file_content)
                gc.collect()
                # Remove saved file
                # try:
                #     os.remove(settings.MEDIA_ROOT + '/' + new_file.name)
                # except OSError:
                #     pass
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            data['form_is_valid'] = False
    else:
        form = UploadFileForm()

    template_name = 'dashboard/include/partial_file_upload.html'
    data['html_form'] = render_to_string(template_name,
                                         {'form': form, 'url_upload': url},
                                         request=request)
    return JsonResponse(data)


@login_required(login_url='/auth/login/')
def download_file(request):
    """Download file - Get file as object from cloud"""
    username = request.user.username
    file = File.objects.filter(owner__username=username). \
        get(id=request.POST.get('download_file'))
    file_content = objects.download_file(file)
    if file_content:
        messages.info(request, 'Download file %s successfully!' % file.name)
        response = HttpResponse(file_content,
                                content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=%s' % smart_str(file.name)
        return response
    else:
        messages.error(request, 'Download file %s failed' % file.name)
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='/auth/login/')
def refresh_status(request):
    username = request.user.username
    file_id = request.GET.get('file_id')
    file = File.objects.filter(owner__username=username).get(id=file_id)
    objects.set_status_file(request, file)
    STATUS = {
        1: 'UPDATE',
        2: 'NOT_UPDATE',
        3: 'AVAILABLE',
        4: 'NOT_AVAILABLE'
    }
    status = STATUS[file.status]
    result = {'status': status}
    return JsonResponse(result)
