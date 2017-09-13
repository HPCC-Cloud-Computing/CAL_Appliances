from django import forms
from django.core import validators
from django.db.models import Q
from .models import User


class UserForm(forms.Form):
    user_name = forms.CharField(label="User name", min_length=4, max_length=30,
                                required=True,
                                widget=forms.TextInput(
                                    attrs={
                                        'placeholder': 'Enter your user name'
                                    }))

    email = forms.CharField(label="Email", required=True,
                            validators=[validators.EmailValidator, ],
                            widget=forms.TextInput(
                                attrs={
                                    'placeholder': 'Enter your email here'
                                }))

    password = forms.CharField(label="Password", min_length=4, max_length=128,
                               required=True,
                               widget=forms.PasswordInput(attrs={
                                   'placeholder': 'Enter your password'
                               }))

    retype_password = forms.CharField(label="Retype password", min_length=8,
                                      max_length=128,
                                      widget=forms.PasswordInput(attrs={
                                          'placeholder': 'Repeat your password'
                                      }))

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        user_name = cleaned_data.get('user_name')
        email = cleaned_data.get('email')
        try:
            validators.validate_email(email)
        except forms.ValidationError:
            self.add_error('email', 'Invalid email format')
        duplicated_users = User.objects.filter(username=user_name).all()
        if len(duplicated_users) > 0:
            self.add_error('user_name', 'This user is existed')
        duplicated_emails = User.objects.filter(email=email).all()
        if len(duplicated_emails) > 0:
            self.add_error('email', 'This email is existed')
        password = cleaned_data.get("password")
        retype_password = cleaned_data.get("retype_password")
        if password != retype_password:
            msg = "Password and retype password must match"
            self.add_error('password', msg)
            self.add_error('retype_password', msg)
        return cleaned_data


class UserProfileForm(forms.Form):
    company = forms.CharField(label='Company', max_length=30,
                              required=False,
                              widget=forms.TextInput(
                                  attrs={
                                      'placeholder':
                                          'Enter your company name here'
                                  }))


class LoginForm(forms.Form):
    user_name_email = forms.CharField(
        label="User name or email", min_length=4, max_length=30,
        required=True, widget=forms.TextInput(
            attrs={
                'placeholder': 'Enter your user name'
                               'or email'
            }))
    password = forms.CharField(label="Password", min_length=4, max_length=128,
                               required=True,
                               widget=forms.PasswordInput(attrs={
                                   'placeholder': 'Enter your password'
                               }))

    def clean(self):
        cleaned_data = super(LoginForm, self).clean()
        user_name_email = cleaned_data.get('user_name_email')
        password = cleaned_data.get("password")
        exist_user = User.objects.filter(
            Q(username=user_name_email) | Q(email=user_name_email)).first()
        if not exist_user:
            self.add_error('user_name_email', 'Invalid User')
        else:
            if exist_user.check_password(password) is False:
                self.add_error('password', 'Password is not correct')
        return cleaned_data
