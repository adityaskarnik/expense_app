from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')
    firstname = forms.CharField(max_length=254, help_text='Required. Inform a name.')
    lastname = forms.CharField(max_length=254, help_text='Required. Inform a valid name.')

    class Meta:
        model = User
        fields = ('firstname', 'lastname', 'username', 'email', 'password1')


class CustomUserCreationForm(forms.Form):
    firstname = forms.CharField(label='Enter Firstname', min_length=4, max_length=150)
    lastname = forms.CharField(label='Enter Lastname', min_length=4, max_length=150)
    username = forms.CharField(label='Enter Username', min_length=4, max_length=150)
    email = forms.EmailField(label='Enter email')
    password1 = forms.CharField(label='Enter password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm password', widget=forms.PasswordInput)

    def clean_firstname(self):
        firstname = self.cleaned_data['firstname']
        return firstname

    def clean_lastname(self):
        lastname = self.cleaned_data['lastname']
        return lastname

    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        r = User.objects.filter(username=username)
        if r.count():
            raise  ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        r = User.objects.filter(email=email)
        if r.count():
            raise  ValidationError("Email already exists")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError("Password don't match")

        return password2

    def save(self, commit=True):
        user = User.objects.create_user(
            self.cleaned_data['username'],
            self.cleaned_data['email'],
            self.cleaned_data['password1'],
            first_name=self.cleaned_data['firstname'],
            last_name=self.cleaned_data['lastname'],
        )
        return user