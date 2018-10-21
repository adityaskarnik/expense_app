from django.apps import AppConfig
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User


class ExpenseAppConfig(AppConfig):
    name = 'expense_app'

class UserCreationForm(UserCreationForm):

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email')

class UserChangeForm(UserChangeForm):

    class Meta:
        model = User
        fields = ('username', 'email')