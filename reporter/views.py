from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def home(request):
    """主页视图，需要登录才能访问"""
    return render(request, 'reporter/home.html')
