from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login

from .forms import NewUserForm

# Create your views here.
def home(request):

    user = request.user
    return render(request,'home.html',context={'user':user})

def register_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			print("Registration successful.")
			return redirect("/")
		print("Unsuccessful registration. Invalid information.")
	
	form = NewUserForm()
	print(form)
	return render(request=request, template_name="registration/register.html", context={"register_form":form})