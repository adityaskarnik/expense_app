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

cwd = os.getcwd()
User = get_user_model()

# Create your views here.
@login_required
def home(request):
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
    print(cwd+'/expense_data_new.json')
    with open(cwd+'/expense_data_new.json') as d:
        data = json.loads(d.read())
    totalDataInDB = Expenses.objects.all().count()
    if (len(data) > totalDataInDB):
        for i in range(totalDataInDB, len(data)):
            # print("inside for:")
            #{'Date': '2017/01/23', 'Amount': -20, 'Category': 'Food & Drinks', 
            # 'Sub Category': 'Snack', 'Payment Method': 'Cash', 'Description': '', 
            # 'Ref/Check No': '', 'Payee / Payer': '', 'Status': 'Uncleared', 
            # 'Receipt Picture': '', 'Account': 'Shopping Expense', 'Tag': '', 
            # 'Tax': '', 'Mileage': ''}
            # TODO in case of no table found operational error occurs delete the DB file
            # TODO this for traccking changes in the csv from old to new
            import pandas
            # print("I",i, data[i]['Date'])
            # This is TODO-ne adding to databse from json
            p = Expenses(date=data[i]['Date'], amount=data[i]['Amount'], category=data[i]['Category'], 
            sub_category=data[i]['Sub Category'], payment_method=data[i]['Payment Method'],
            description=data[i]['Description'], ref_checkno=data[i]['Ref/Check No'], payee_payer=data[i]['Payee / Payer'], 
            status=data[i]['Status'], receipt_picture=data[i]['Receipt Picture'],
            account=data[i]['Account'], tag=data[i]['Tag'], tax=data[i]['Tax'], mileage=data[i]['Mileage'])
            p.save()
            print(p.id)
    else:
        print("No change in the input data")
            
            
    return render(request, 'dashboard.html', {'data':data})

# with open(cwd+'/expense_data.json') as d:
#     data = json.load(d)

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