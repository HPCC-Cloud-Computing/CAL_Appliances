from django import forms
from django.contrib.admin import widgets
from django.contrib.auth.models import User

from mcs.apps.authentication.models import UserProfile
from mcs.apps.user_dashboard.models import File


class CreateFolderForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ('name',)
        widgets = {
            'name': widgets.AdminTextInputWidget,
        }


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ('content',)


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('image', 'bio', 'company', 'location')