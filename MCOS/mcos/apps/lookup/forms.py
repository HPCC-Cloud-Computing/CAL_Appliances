from django import forms


class UploadCloudConfigsForm(forms.Form):
    cloud_configs = forms.FileField()
