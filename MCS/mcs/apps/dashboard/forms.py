from django import forms
from django.contrib.admin import widgets

from dashboard.models import File


class CreateFolderForm(forms.ModelForm):

    class Meta:
        model = File
        fields = ('name', )
        widgets = {
            'name': widgets.AdminTextInputWidget,
        }


class UploadFileForm(forms.ModelForm):

    class Meta:
        model = File
        fields = ('content',)
