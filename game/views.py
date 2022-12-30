from django.shortcuts import render

# Create your views here.
def game(request):
    return render(request,'game.html')

def login(request):
    return render(request, 'login.html')