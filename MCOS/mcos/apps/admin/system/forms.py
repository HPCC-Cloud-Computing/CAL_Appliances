from django.contrib.admin import widgets
from django.forms import Form
from django import forms
from django.core import validators
from django.db.models import Q
from .models import SystemCluster


class ConnectToSystemForm(Form):
    cluster_id = forms.CharField(label='cluster_id', max_length=1000,
                                 required=True)
    cluster_name = forms.CharField(label='cluster_name', max_length=1000,
                                   required=True)
    cluster_ip = forms.CharField(label='cluster_ip', max_length=1000,
                                 required=True)
    cluster_port = forms.CharField(label='cluster_port', max_length=1000,
                                   required=True)
    service_info = forms.CharField(label='service_info', max_length=3000,
                                   required=True)

    def clean(self):
        cleaned_data = super(ConnectToSystemForm, self).clean()
        cluster_id = cleaned_data.get('cluster_id')
        cluster_name = cleaned_data.get('cluster_name')
        cluster_ip = cleaned_data.get('cluster_ip')
        cluster_port = cleaned_data.get('cluster_port')
        duplicated_clusters = SystemCluster.objects.filter(
            Q(id=cluster_id) | Q(name=cluster_name) |
            (Q(address_ip=cluster_ip) & Q(address_port=cluster_port))
        ).all()
        if len(duplicated_clusters) > 0:
            raise forms.ValidationError('duplicate name or address')
        return cleaned_data


class AddNewClusterForm(ConnectToSystemForm):
    request_cluster_id = forms.CharField(label='request_cluster_id',
                                         max_length=1000,
                                         required=True)

    def clean(self):
        cleaned_data = super(AddNewClusterForm, self).clean()
        return cleaned_data


class ReleaseAddClusterPermForm(Form):
    request_cluster_id = forms.CharField(label='request_cluster_id',
                                         max_length=1000,
                                         required=True)

    def clean(self):
        cleaned_data = super(ReleaseAddClusterPermForm, self).clean()
        return cleaned_data


class GainAddClusterPermissionForm(Form):
    request_cluster_id = forms.CharField(
        label='request_cluster_id', max_length=100, required=True)

    def clean(self):
        cleaned_data = super(GainAddClusterPermissionForm, self).clean()
        return cleaned_data


class NewClusterDataForm(Form):
    cluster_name = forms.CharField(label='cluster_name', max_length=100,
                                   required=True)
    cluster_address = forms.CharField(label='cluster_address', max_length=100,
                                      required=True)

    def clean(self):
        cleaned_data = super(NewClusterDataForm, self).clean()
        cluster_name = cleaned_data.get('cluster_name')
        cluster_address = cleaned_data.get('cluster_address')
        duplicated_clusters = SystemCluster.objects.filter(
            Q(name=cluster_name) | Q(address=cluster_address)).all()
        if len(duplicated_clusters) > 0:
            raise forms.ValidationError('duplicate name or address')
        return cleaned_data
