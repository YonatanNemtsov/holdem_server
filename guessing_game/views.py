from django.shortcuts import render
from django.contrib.auth import get_user_model
# Create your views here.
def home(request):

    user = request.user
    return render(request,'home.html',context={'user':user})
