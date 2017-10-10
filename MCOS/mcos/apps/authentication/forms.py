from django import forms
from django.core import validators


class UserRegisterForm(forms.Form):
    user_name = forms.CharField(label="User name", min_length=4, max_length=30,
                                required=True,
                                widget=forms.TextInput(
                                    attrs={
                                        'placeholder': 'Enter your user name'
                                    }))
    password = forms.CharField(label="Password", min_length=4, max_length=128,
                               required=True,
                               widget=forms.PasswordInput(attrs={
                                   'placeholder': 'Enter your password'
                               }))
    retype_password = forms.CharField(label="Retype password", min_length=4,
                                      max_length=128,
                                      widget=forms.PasswordInput(attrs={
                                          'placeholder': 'Repeat your password'
                                      }))

    def clean(self):
        cleaned_data = super(UserRegisterForm, self).clean()
        # user_name = cleaned_data.get('user_name')
        password = cleaned_data.get("password")
        retype_password = cleaned_data.get("retype_password")
        if password != retype_password:
            msg = "Password and retype password must match"
            self.add_error('password', msg)
            self.add_error('retype_password', msg)
        return cleaned_data


class LoginForm(forms.Form):
    user_name = forms.CharField(
        label="User Name", min_length=4, max_length=30,
        required=True, widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter your user name'
            }))
    password = forms.CharField(label="Password", min_length=4, max_length=128,
                               required=True,
                               widget=forms.PasswordInput(attrs={
                                   'placeholder': 'Enter your password'
                               }))
    next_url = forms.CharField(widget=forms.HiddenInput(), required=False)

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        # username = cleaned_data.get('user_name')
        # password = cleaned_data.get("password")
        return cleaned_data
