from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, login
from django.contrib.auth.models import User
from game.models import UserAccount, GameTable
from .forms import NewUserForm

# Create your views here.
def home(request):
	user = request.user
	tables = [{'id':table.id,'name':table.table_name,'small_blind':table.config['small_blind'], 'big_blind':2*table.config['small_blind']} for table in GameTable.objects.all()]
	context = {'user':user,'tables':tables}
	if user.is_authenticated:
		context['balance'] = UserAccount.objects.get(user=user).balance
	return render(request,'home.html',context=context)

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


def registration_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            user = User.objects.create_user(username=username, password=password)
            user.save()
            account = UserAccount.objects.create(user=user)
            account.save()
            return redirect('/')  # You need to define this URL
        else:
            error_message = "Passwords do not match"
    else:
        error_message = ""

    return render(request, 'registration/register.html', {'error_message': error_message})