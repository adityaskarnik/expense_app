from django.shortcuts import render, redirect
import pytz
from django.template.loader import get_template, render_to_string
from datetime import datetime, timezone
import dateutil.parser
from .apps import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
import json
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login
from django import forms
from .forms import SignUpForm
from django.contrib import auth
from django.contrib.auth.decorators import login_required
import os
from .models import Expenses
from django.core import serializers

cwd = os.getcwd()
User = get_user_model()

# Create your views here.
@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('/expense_app')
    else:
        form = SignUpForm()
    return render(request, 'register.html', {'form': form})

def index(request):
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    str_now = str(now)
    new_now = str(datetime.strptime(str_now.split(".")[0], '%Y-%m-%d %H:%M:%S'))
    now = dateutil.parser.parse(new_now)
    # html = "<html><body>It is now %s</body></html>" % now
    t = get_template('dashboard.html')
    # html = t.render({'current_date': now})
    print(cwd+'/expense_data.json')
    with open(cwd+'/expense_data.json') as d:
        data = json.loads(d.read())
    return render(request, 'dashboard.html', {'data':data})

# with open(cwd+'/expense_data.json') as d:
#     data = json.load(d)

def ajax_loaddata(request):
    # with open(cwd+'/expense_data.json') as d:
        # data = json.loads(d.read())
    data = Expenses.objects.all()
    json_data = serializers.serialize('json', data)
    return HttpResponse(json_data, content_type='application/json')