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
from django.views.decorators.http import require_POST
import os
from decimal import Decimal, InvalidOperation
from .models import Expenses
from django.core import serializers
from django.db.models import Sum, Q
from django.http import JsonResponse
from check_new_data import check_new_data, download_new_attachment
from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
import logging
from elasticsearch import Elasticsearch
from django.core.paginator import Paginator
from django.db import models
from .categorization import classify_transaction, learn_merchant_mapping

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()
app = Celery('check_expense_file',
             broker='amqp://rabbitmq:rabbitmq@rabbitmq:5672//')

cwd = os.getcwd()
User = get_user_model()

index_name = 'expense_mail_checker'
doc_type = 'mailchecker'
es = Elasticsearch(
    ['http://10.10.0.6:9200'],
    http_auth=('elastic', os.getenv('ELASTIC_PASSWORD', '')),
    headers={"Content-Type": "application/json"}
)

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour='*/1'),update_data.s())
    # sender.add_periodic_task(crontab(minute='*'),mail_checker.s())

# Create your views here.
@login_required
def home(request):
    if (len(Expenses.objects.all()) > 0):
        food = int(abs((Expenses.objects.filter(category='Food').aggregate(Sum('amount'))['amount__sum']) or 0))
        travel = int(abs((Expenses.objects.filter(category='Travel').aggregate(Sum('amount'))['amount__sum']) or 0))
        personal = int(abs((Expenses.objects.filter(category='Personal').aggregate(Sum('amount'))['amount__sum']) or 0))
        savings = int(abs((Expenses.objects.filter(category='Savings').aggregate(Sum('amount'))['amount__sum']) or 0))
        entertainment = int(abs((Expenses.objects.filter(category='Entertainment').aggregate(Sum('amount'))['amount__sum']) or 0))
        household = int(abs((Expenses.objects.filter(category='Household').aggregate(Sum('amount'))['amount__sum']) or 0))
        healthcare = int(abs((Expenses.objects.filter(category='Health Care').aggregate(Sum('amount'))['amount__sum']) or 0))
        utilities = int(abs((Expenses.objects.filter(category='Utilities').aggregate(Sum('amount'))['amount__sum']) or 0))
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
def update_data(request=None):
    filepath = download_new_attachment()
    if (filepath != None):
        new_data = check_new_data(filepath)
        if (new_data > 0):
            file = cwd+'/expense_data.json'
            with open(file) as d:
                data = json.loads(d.read())
                for i in range((len(data)-new_data),len(data)):
                    csv_category = data[i].get('Category', 'Unknown') or 'Unknown'
                    csv_sub_category = data[i].get('Sub Category', 'Unknown') or 'Unknown'
                    payee = data[i].get('Payee / Payer', '')
                    description = data[i].get('Description', '')

                    predicted_category, predicted_sub_category, _, _ = classify_transaction(payee, description)
                    final_category = csv_category
                    final_sub_category = csv_sub_category

                    if final_category in ('', 'Unknown') and predicted_category not in ('', 'Unknown'):
                        final_category = predicted_category
                        final_sub_category = predicted_sub_category

                    if final_category not in ('', 'Unknown'):
                        learn_merchant_mapping(payee or description, final_category, final_sub_category, source='csv_import')

                    p = Expenses(date=data[i]['Date'], amount=data[i]['Amount'], category=final_category,
                    sub_category=final_sub_category, payment_method=data[i]['Payment Method'],
                    description=data[i]['Description'], ref_checkno=data[i]['Ref/Check No'], payee_payer=data[i]['Payee / Payer'], 
                    status=data[i]['Status'], receipt_picture=data[i]['Receipt Picture'],
                    account=data[i]['Account'], tag=data[i]['Tag'], tax=data[i]['Tax'], mileage=data[i]['Mileage'])
                    p.save()
                    expense = {}
                    expense['date'] = data[i]['Date']
                    expense['amount'] = data[i]['Amount']
                    expense['category'] = final_category
                    expense['sub_category'] = final_sub_category
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
                    es.index(index=index_name, body=expense)
                return JsonResponse({'data': data, 'length': len(data), 'new': 'true'})
    else:
        logging.info("No change in the input data")
        data = []
        file = cwd+'/expense_data.json'
        with open(file) as d:
            if not d: data = json.loads(d.read())
            return JsonResponse({'data': data, 'new': 'false'})

def ajax_loaddata(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    # Filter your data based on the search value
    queryset = Expenses.objects.all()
    if search_value:
        search_query = Q()
        for field in Expenses._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                search_query |= Q(**{f"{field.name}__icontains": search_value})
        queryset = queryset.filter(search_query)


    queryset = queryset.order_by('-date')
    # Paginate your data
    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page = paginator.get_page(page_number)

    data = list(page.object_list.values())

    response = {
        "draw": draw,
        "recordsTotal": paginator.count,
        "recordsFiltered": paginator.count,
        "data": data,
    }
    return JsonResponse(response)


@login_required
def insert_data(request):
    p = Expenses(date="10/10/1991", amount="100", category="Personal", sub_category="nothing personal", payment_method="",
        description="", ref_checkno="", payee_payer="", status="", receipt_picture="",
        account="", tag="", tax="", mileage="")
    p.save


@login_required
@require_POST
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

@login_required
@require_POST
def add_expense(request):
    requested_category = request.POST.get('category') or 'Unknown'
    requested_sub_category = request.POST.get('subcategory') or 'Unknown'
    custom_sub_category = (request.POST.get('custom_subcategory') or '').strip()
    payee = request.POST.get('payee') or ''
    description = request.POST.get('description') or ''
    expense_id = request.POST.get('expense_id')
    amount_raw = (request.POST.get('amount') or '').replace(',', '').strip()

    try:
        amount_value = Decimal(amount_raw).quantize(Decimal('0.01'))
    except (InvalidOperation, TypeError):
        return JsonResponse({'error': 'Invalid amount. Please enter a valid decimal number.'}, status=400)

    if requested_sub_category == '__custom__':
        requested_sub_category = custom_sub_category or 'Unknown'

    predicted_category, predicted_sub_category, _, _ = classify_transaction(payee, description)
    final_category = requested_category
    final_sub_category = requested_sub_category

    if final_category in ('', 'Unknown') and predicted_category not in ('', 'Unknown'):
        final_category = predicted_category
        final_sub_category = predicted_sub_category

    if final_category not in ('', 'Unknown'):
        learn_merchant_mapping(payee or description, final_category, final_sub_category, source='web_add')

    # Check if editing existing expense or creating new one
    if expense_id:
        # Update existing expense
        try:
            p = Expenses.objects.get(id=expense_id)
            p.date = request.POST.get('date')
            p.amount = amount_value
            p.category = final_category
            p.sub_category = final_sub_category
            p.payment_method = request.POST.get('method')
            p.description = request.POST.get('description')
            p.ref_checkno = request.POST.get('checkno')
            p.payee_payer = request.POST.get('payee')
            p.status = request.POST.get('status')
            p.receipt_picture = ''
            p.account = request.POST.get('account')
            p.tag = request.POST.get('tag')
            p.tax = request.POST.get('tax')
            p.mileage = ''
            p.save()
        except Expenses.DoesNotExist:
            return JsonResponse({'error': 'Expense not found'}, status=404)
    else:
        # Create new expense
        p = Expenses(date=request.POST.get('date'), amount=amount_value, category=final_category,
                sub_category=final_sub_category, payment_method=request.POST.get('method'),
                description=request.POST.get('description'), ref_checkno=request.POST.get('checkno'), payee_payer=request.POST.get('payee'), 
                status=request.POST.get('status'), receipt_picture='',
                account=request.POST.get('account'), tag=request.POST.get('tag'), tax=request.POST.get('tax'), mileage='')
        p.save()
    
    expense = {}
    expense['date'] = request.POST.get('date')
    expense['amount'] = str(amount_value)
    expense['category'] = final_category
    expense['sub_category'] = final_sub_category
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
    es.index(index=index_name, body=expense)
    
    return JsonResponse({'data':"Data"})

