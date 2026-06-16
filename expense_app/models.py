from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
class User(AbstractUser):
    def __str__(self):
        return self.email
    
class Expenses(models.Model):
    date = models.CharField(max_length=500)
    amount = models.IntegerField()
    category = models.CharField(max_length=500)
    sub_category = models.CharField(max_length=500)
    payment_method = models.CharField(max_length=500)
    description = models.CharField(max_length=500)
    ref_checkno = models.CharField(max_length=500)
    payee_payer = models.CharField(max_length=500)
    status = models.CharField(max_length=500)
    receipt_picture = models.CharField(max_length=500)
    account = models.CharField(max_length=500)
    tag = models.CharField(max_length=500)
    tax = models.CharField(max_length=500)
    mileage = models.CharField(max_length=500)

    class Meta:
        db_table = "Expenses"
    
    def __str__(self):
        return '%s %s %s %s %s %s %s %s %s %s %s %s %s %s' %(self.date, self.amount, self.category, self.sub_category, self.payment_method,
        self.description, self.ref_checkno, self.payee_payer, self.status, self.receipt_picture,
        self.account, self.tag, self.tax, self.mileage)


class MerchantCategoryMapping(models.Model):
    merchant_key = models.CharField(max_length=500, unique=True)
    merchant_display = models.CharField(max_length=500)
    category = models.CharField(max_length=500)
    sub_category = models.CharField(max_length=500, default='Unknown')
    source = models.CharField(max_length=100, default='manual')
    confidence = models.FloatField(default=1.0)
    times_used = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'MerchantCategoryMapping'

    def __str__(self):
        return '%s -> %s/%s' %(self.merchant_display, self.category, self.sub_category)