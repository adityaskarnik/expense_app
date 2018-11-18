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
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django import forms
from .forms import SignUpForm
from django.contrib import auth
from django.contrib.auth.decorators import login_required

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
            return redirect('home')
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
    with open('/home/adityakarnik/console_projects/expense_manager/expense_data.json') as d:
        data = json.loads(d.read())
    
    return render(request, 'dashboard.html', {'data':data})

with open('/home/adityakarnik/console_projects/expense_manager/expense_data.json') as d:
    data = json.load(d)
