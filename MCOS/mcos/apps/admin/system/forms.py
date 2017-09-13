from django.contrib.admin import widgets
from django.forms import Form
from django import forms
from django.core import validators
from django.db.models import Q
from .models import SystemNode


class ConnectToSystemForm(Form):
    node_name = forms.CharField(label='node_name', max_length=100,
                                required=True)
    node_address = forms.CharField(label='node_address', max_length=100,
                                   required=True)

    def clean(self):
        cleaned_data = super(ConnectToSystemForm, self).clean()
        node_name = cleaned_data.get('node_name')
        node_address = cleaned_data.get('node_address')
        duplicated_nodes = SystemNode.objects.filter(
            Q(name=node_name) | Q(address=node_address)).all()
        if len(duplicated_nodes) > 0:
            raise forms.ValidationError('duplicate name or address')


class NewNodeDataForm(Form):
    node_name = forms.CharField(label='node_name', max_length=100,
                                required=True)
    node_address = forms.CharField(label='node_address', max_length=100,
                                   required=True)

    def clean(self):
        cleaned_data = super(NewNodeDataForm, self).clean()
        node_name = cleaned_data.get('node_name')
        node_address = cleaned_data.get('node_address')
        duplicated_nodes = SystemNode.objects.filter(
            Q(name=node_name) | Q(address=node_address)).all()
        if len(duplicated_nodes) > 0:
            raise forms.ValidationError('duplicate name or address')