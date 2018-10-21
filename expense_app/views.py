from django.shortcuts import render
import pytz
from django.template.loader import get_template
from datetime import datetime, timezone
import dateutil.parser
from .apps import UserCreationForm
from django.urls import reverse_lazy
from django.views import generic
from django.http import HttpResponse

# Create your views here.


def index(request):
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    str_now = str(now)
    new_now = str(datetime.strptime(str_now.split(".")[0], '%Y-%m-%d %H:%M:%S'))
    now = dateutil.parser.parse(new_now)
    # html = "<html><body>It is now %s</body></html>" % now
    t = get_template('dashboard.html')
    html = t.render({'current_date': now})
    return HttpResponse(html)

class SignUp(generic.CreateView):
    form_class = UserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'