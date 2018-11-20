from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .apps import UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model

# class UserAdmin(UserAdmin):
#     add_form = UserCreationForm
#     form = UserChangeForm
#     model = User
#     list_display = ['email', 'username',]

# admin.site.register(User, UserAdmin)

User = get_user_model()