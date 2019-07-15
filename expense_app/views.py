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
from django.db.models import Sum
from django.http import JsonResponse
from check_new_data import check_new_data, download_new_attachment
from celery import Celery
from celery.schedules import crontab

app = Celery('check_expense_file')

cwd = os.getcwd()
User = get_user_model()

from elasticsearch import Elasticsearch
index = 'expensemailchecker'
doc_type = 'mail_checker'
es = Elasticsearch('elastic:Dscw1800@elasticsearch:9200/')

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour='*/1'),mail_checker.s())
    # sender.add_periodic_task(crontab(minute='*'),mail_checker.s())

# Create your views here.
@login_required
def home(request):
    if (len(Expenses.objects.all()) > 0):
        food = int(abs(Expenses.objects.filter(category='Food').aggregate(Sum('amount'))['amount__sum']))
        travel = int(abs(Expenses.objects.filter(category='Travel').aggregate(Sum('amount'))['amount__sum']))
        personal = int(abs(Expenses.objects.filter(category='Personal').aggregate(Sum('amount'))['amount__sum']))
        savings = int(abs(Expenses.objects.filter(category='Savings').aggregate(Sum('amount'))['amount__sum']))
        entertainment = int(abs(Expenses.objects.filter(category='Entertainment').aggregate(Sum('amount'))['amount__sum']))
        household = int(abs(Expenses.objects.filter(category='Household').aggregate(Sum('amount'))['amount__sum']))
        healthcare = int(abs(Expenses.objects.filter(category='Health Care').aggregate(Sum('amount'))['amount__sum']))
        utilities = int(abs(Expenses.objects.filter(category='Utilities').aggregate(Sum('amount'))['amount__sum']))
        return render(request, 'home.html', {'food':food, 'travel':travel, 'personal':personal,
                                            'savings':savings, 'entertainment':entertainment,
                                            'household':household, 'healthcare':healthcare,
                                            'utilities':utilities})
    else:
        return render(request, 'home.html', {'food':0, 'travel':0, 'personal':0,
                                            'savings':0, 'entertainment':0,
                                            'household':0, 'healthcare':0,
                                            'utilities':0})

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
    data = []
    file = cwd+'/expense_data.json'
    with open(file) as d:
        if not d: data = json.loads(d.read())
        return render(request, 'dashboard.html', {'data':data})

@app.task
def update_data(request):
    filepath = download_new_attachment()
    if (filepath != None):
        new_data = check_new_data(filepath)
        if (new_data > 0):
            file = cwd+'/expense_data.json'
            with open(file) as d:
                data = json.loads(d.read())
                for i in range((len(data)-new_data),len(data)):
                    p = Expenses(date=data[i]['Date'], amount=data[i]['Amount'], category=data[i]['Category'], 
                    sub_category=data[i]['Sub Category'], payment_method=data[i]['Payment Method'],
                    description=data[i]['Description'], ref_checkno=data[i]['Ref/Check No'], payee_payer=data[i]['Payee / Payer'], 
                    status=data[i]['Status'], receipt_picture=data[i]['Receipt Picture'],
                    account=data[i]['Account'], tag=data[i]['Tag'], tax=data[i]['Tax'], mileage=data[i]['Mileage'])
                    p.save()
                    expense = {}
                    expense['date'] = data[i]['Date']
                    expense['amount'] = data[i]['Amount']
                    expense['category'] = data[i]['Category']
                    expense['sub_category'] = data[i]['Sub Category']
                    expense['payment_method'] = data[i]['Payment Method']
                    expense['description'] = data[i]['Description']
                    expense['ref_checkno'] = data[i]['Ref/Check No']
                    expense['payee_payer'] = data[i]['Payee / Payer']
                    expense['status'] = data[i]['Status']
                    expense['receipt_picture'] = data[i]['Receipt Picture']
                    expense['account'] = data[i]['Account']
                    expense['tag'] = data[i]['Tag']
                    expense['tax'] = data[i]['Tax']
                    expense['mileage'] = data[i]['Mileage']
                    es.index(index=index, doc_type=doc_type, body=expense)
                return JsonResponse({'data': data, 'length': len(data), 'new': 'true'})
    else:
        print("No change in the input data")
        data = []
        file = cwd+'/expense_data.json'
        with open(file) as d:
            if not d: data = json.loads(d.read())
            return JsonResponse({'data': data, 'new': 'false'})

def ajax_loaddata(request):
    # with open(cwd+'/expense_data.json') as d:
        # data = json.loads(d.read())
    data = Expenses.objects.all()
    json_data = serializers.serialize('json', data)
    return HttpResponse(json_data, content_type='application/json')


def insert_data(request):
    p = Expenses(date="10/10/1991", amount="100", category="Personal", sub_category="nothing personal", payment_method="",
        description="", ref_checkno="", payee_payer="", status="", receipt_picture="",
        account="", tag="", tax="", mileage="")
    p.save


def delete_data(request):
    p = Expenses.objects.all().delete()
    open(cwd+'/expense_data.json', 'w').close()
    return render(request, 'dashboard.html', {'p':p})


def date_wise_expense(request):
    food = Expenses.objects.exclude(category='Income').filter(category="Food").filter(date__range=[request.GET['startdate'], request.GET['enddate']]).aggregate(Sum('amount'))['amount__sum']
    travel = Expenses.objects.exclude(category='Income').filter(category="Travel").filter(date__range=[request.GET['startdate'], request.GET['enddate']]).aggregate(Sum('amount'))['amount__sum']
    personal = Expenses.objects.exclude(category='Income').filter(category="Personal").filter(date__range=[request.GET['startdate'], request.GET['enddate']]).aggregate(Sum('amount'))['amount__sum']
    savings = Expenses.objects.exclude(category='Income').filter(category="Savings").filter(date__range=[request.GET['startdate'], request.GET['enddate']]).aggregate(Sum('amount'))['amount__sum']
    entertainment = Expenses.objects.exclude(category='Income').filter(category="Entertainment").filter(date__range=[request.GET['startdate'], request.GET['enddate']]).aggregate(Sum('amount'))['amount__sum']
    household = Expenses.objects.exclude(category='Income').filter(category="Household").filter(date__range=[request.GET['startdate'], request.GET['enddate']]).aggregate(Sum('amount'))['amount__sum']
    healthcare = Expenses.objects.exclude(category='Income').filter(category="Health Care").filter(date__range=[request.GET['startdate'], request.GET['enddate']]).aggregate(Sum('amount'))['amount__sum']
    utilities = Expenses.objects.exclude(category='Income').filter(category="Utilities").filter(date__range=[request.GET['startdate'], request.GET['enddate']]).aggregate(Sum('amount'))['amount__sum']
    return JsonResponse({'food':food, 'travel':travel, 'personal':personal,
                                        'savings':savings, 'entertainment':entertainment,
                                        'household':household, 'healthcare':healthcare,
                                        'utilities':utilities})

def startdate_enddate(request):
    startdate = Expenses.objects.order_by('date')[0].date
    enddate = Expenses.objects.latest('date').date
    return JsonResponse({'startdate': startdate, 'enddate': enddate})


def add_expense(request):
    p = Expenses(date=request.POST.get('date'), amount=request.POST.get('amount'), category=request.POST.get('category'), 
            sub_category=request.POST.get('subcategory'), payment_method=request.POST.get('method'),
            description=request.POST.get('description'), ref_checkno=request.POST.get('checkno'), payee_payer=request.POST.get('payee'), 
            status=request.POST.get('status'), receipt_picture='',
            account=request.POST.get('account'), tag=request.POST.get('tag'), tax=request.POST.get('tax'), mileage='')
    p.save()
    expense = {}
    expense['date'] = request.POST.get('date')
    expense['amount'] = request.POST.get('amount')
    expense['category'] = request.POST.get('category')
    expense['sub_category'] = request.POST.get('subcategory')
    expense['payment_method'] = request.POST.get('method')
    expense['description'] = request.POST.get('description')
    expense['ref_checkno'] = request.POST.get('checkno')
    expense['payee_payer'] = request.POST.get('payee')
    expense['status'] = request.POST.get('status')
    expense['receipt_picture'] = ''
    expense['account'] = request.POST.get('account')
    expense['tag'] = request.POST.get('tag')
    expense['tax'] = request.POST.get('tax')
    expense['mileage'] = ''
    es.index(index=index, doc_type=doc_type, body=expense)
    return JsonResponse({'data':"Data"})

